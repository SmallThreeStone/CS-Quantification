from datetime import datetime, timedelta

from app.models import Item, MonitorPool, Platform, StrategyConfig
from app.services.market_provider import Quote, SteamMarketProvider
from app.services.market_service import MarketService


def test_collect_due_pools_only_collects_due_pool_items(db_session):
    platform = Platform(code="steam", name="Steam")
    due_pool = MonitorPool(name="重点池", interval_minutes=10, last_collected_at=None)
    waiting_pool = MonitorPool(name="观察池", interval_minutes=30, last_collected_at=datetime.utcnow())
    db_session.add_all([platform, due_pool, waiting_pool, StrategyConfig(name="default")])
    db_session.flush()
    db_session.add(Item(market_hash_name="due", display_name="到期", pool_id=due_pool.id, is_active=True))
    db_session.add(Item(market_hash_name="waiting", display_name="未到期", pool_id=waiting_pool.id, is_active=True))
    db_session.commit()

    MarketService(db_session).collect_due_pools()

    assert len(due_pool.items[0].snapshots) == 1
    assert len(waiting_pool.items[0].snapshots) == 0
    assert due_pool.last_collected_at is not None


def test_collect_due_pools_collects_again_after_interval(db_session):
    platform = Platform(code="steam", name="Steam")
    pool = MonitorPool(name="重点池", interval_minutes=10, last_collected_at=datetime.utcnow() - timedelta(minutes=11))
    db_session.add_all([platform, pool, StrategyConfig(name="default")])
    db_session.flush()
    db_session.add(Item(market_hash_name="due-again", display_name="再次到期", pool_id=pool.id, is_active=True))
    db_session.commit()

    MarketService(db_session).collect_due_pools()

    assert len(pool.items[0].snapshots) == 1


def test_collect_run_log_records_success(db_session):
    platform = Platform(code="steam", name="Steam")
    pool = MonitorPool(name="重点池", interval_minutes=10)
    db_session.add_all([platform, pool, StrategyConfig(name="default")])
    db_session.flush()
    db_session.add(Item(market_hash_name="log-success", display_name="成功", pool_id=pool.id, is_active=True))
    db_session.commit()

    service = MarketService(db_session)
    service.collect_due_pools()

    assert service.last_run_log is not None
    assert service.last_run_log.status == "success"
    assert service.last_run_log.item_count == 1
    assert service.last_run_log.snapshot_count == 1


def test_collect_run_log_records_failure_without_raising(db_session):
    platform = Platform(code="steam", name="Steam")
    pool = MonitorPool(name="重点池", interval_minutes=10)
    db_session.add_all([platform, pool, StrategyConfig(name="default")])
    db_session.flush()
    db_session.add(Item(market_hash_name="log-failure", display_name="失败", pool_id=pool.id, is_active=True))
    db_session.commit()
    service = MarketService(db_session)
    service.provider = FailingProvider()

    alerts = service.collect_due_pools()

    assert alerts == []
    assert service.last_run_log is not None
    assert service.last_run_log.status == "failed"
    assert service.last_run_log.error_count == 1


def test_collect_run_log_records_source_quality(db_session):
    platform = Platform(code="steam", name="Steam")
    pool = MonitorPool(name="quality-pool", interval_minutes=10)
    db_session.add_all([platform, pool, StrategyConfig(name="default")])
    db_session.flush()
    db_session.add(Item(market_hash_name="quality", display_name="质量", pool_id=pool.id, is_active=True))
    db_session.commit()
    service = MarketService(db_session)
    service.provider = QualityProvider()

    service.collect_due_pools()

    assert service.last_run_log is not None
    assert service.last_run_log.real_field_count == 2
    assert service.last_run_log.fallback_field_count == 4
    assert service.last_run_log.fallback_count == 1


def test_steam_provider_marks_partial_real_fields(monkeypatch):
    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {"success": True, "lowest_price": "¥100.50", "volume": "12", "median_price": "¥99.00"}

    monkeypatch.setattr("app.services.market_provider.httpx.get", lambda *args, **kwargs: Response())

    quote = SteamMarketProvider().fetch_quote("AK-47 | Test")

    quality = quote.raw_payload["source_quality"]
    assert quality["is_fallback"] is False
    assert {"lowest_price", "volume_24h", "avg_price_24h"} <= set(quality["real_fields"])
    assert {"sell_count", "highest_buy_price", "buy_count"} <= set(quality["fallback_fields"])


def test_steam_provider_uses_orderbook_when_item_nameid_is_configured(monkeypatch):
    from app.config import settings

    previous_enabled = settings.steam_orderbook_enabled
    previous_mapping = settings.steam_orderbook_item_nameids
    settings.steam_orderbook_enabled = True
    settings.steam_orderbook_item_nameids = '{"AK-47 | Test": "12345"}'

    class Response:
        def __init__(self, payload):
            self.payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return self.payload

    def fake_get(url, *args, **kwargs):
        if "itemordershistogram" in url:
            return Response(
                {
                    "sell_order_graph": [[101.0, 3, "3"], [102.0, 8, "8"]],
                    "buy_order_graph": [[99.0, 4, "4"], [98.0, 9, "9"]],
                }
            )
        return Response({"success": True, "lowest_price": "¥100.50", "volume": "12", "median_price": "¥99.00"})

    monkeypatch.setattr("app.services.market_provider.httpx.get", fake_get)
    try:
        quote = SteamMarketProvider().fetch_quote("AK-47 | Test")
    finally:
        settings.steam_orderbook_enabled = previous_enabled
        settings.steam_orderbook_item_nameids = previous_mapping

    quality = quote.raw_payload["source_quality"]
    assert quote.sell_count == 8
    assert quote.buy_count == 9
    assert quote.highest_buy_price == 99
    assert {"sell_count", "highest_buy_price", "buy_count"} <= set(quality["real_fields"])
    assert "sell_count" not in quality["fallback_fields"]


def test_steam_provider_records_orderbook_fallback_reason(monkeypatch):
    from app.config import settings

    previous_enabled = settings.steam_orderbook_enabled
    previous_mapping = settings.steam_orderbook_item_nameids
    settings.steam_orderbook_enabled = True
    settings.steam_orderbook_item_nameids = "{}"

    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {"success": True, "lowest_price": "¥100.50", "volume": "12", "median_price": "¥99.00"}

    monkeypatch.setattr("app.services.market_provider.httpx.get", lambda *args, **kwargs: Response())
    try:
        quote = SteamMarketProvider().fetch_quote("AK-47 | Test")
    finally:
        settings.steam_orderbook_enabled = previous_enabled
        settings.steam_orderbook_item_nameids = previous_mapping

    assert "missing steam item_nameid mapping" in quote.raw_payload["orderbook_error"]
    assert {"sell_count", "highest_buy_price", "buy_count"} <= set(quote.raw_payload["source_quality"]["fallback_fields"])


class FailingProvider:
    def fetch_quote(self, market_hash_name: str):
        raise RuntimeError(f"provider failed for {market_hash_name}")


class QualityProvider:
    def fetch_quote(self, market_hash_name: str):
        return Quote(
            market_hash_name=market_hash_name,
            lowest_price=100,
            sell_count=10,
            highest_buy_price=90,
            buy_count=5,
            volume_24h=3,
            avg_price_24h=98,
            captured_at=datetime.utcnow(),
            raw_payload={
                "source_quality": {
                    "real_fields": ["lowest_price", "volume_24h"],
                    "fallback_fields": ["sell_count", "highest_buy_price", "buy_count", "avg_price_24h"],
                    "is_fallback": False,
                }
            },
        )
