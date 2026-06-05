from datetime import datetime, timedelta

from app.models import Item, MonitorPool, Platform, StrategyConfig
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


class FailingProvider:
    def fetch_quote(self, market_hash_name: str):
        raise RuntimeError(f"provider failed for {market_hash_name}")
