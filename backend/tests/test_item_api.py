from fastapi.testclient import TestClient
from datetime import datetime
import json

from app.database import get_db
from app.main import app
from app.models import Alert, Item, MarketSnapshot, MonitorPool, Platform
from tests.test_strategy_api import override_session


def test_item_can_be_created_and_deactivated(db_session):
    pool = MonitorPool(name="重点池", interval_minutes=10)
    db_session.add(pool)
    db_session.commit()
    app.dependency_overrides[get_db] = override_session(db_session)
    client = TestClient(app)

    created = client.post(
        "/api/items",
        json={
            "market_hash_name": "AK-47 | Emerald Pinstripe (Factory New)",
            "display_name": "AK-47 | 翡翠细条纹",
            "exterior": "崭新出厂",
            "category": "rifle",
            "steam_item_nameid": "12345",
            "is_active": True,
            "pool_id": pool.id,
        },
    )
    inactive = client.patch(f"/api/items/{created.json()['id']}/active", params={"is_active": False})
    monitor = client.get("/api/monitor")

    app.dependency_overrides.clear()
    assert created.status_code == 200
    assert created.json()["pool_name"] == "重点池"
    assert created.json()["steam_item_nameid"] == "12345"
    assert inactive.status_code == 200
    assert inactive.json()["is_active"] is False
    assert all(row["id"] != created.json()["id"] for row in monitor.json())


def test_item_rejects_duplicate_market_hash_name(db_session):
    db_session.add(Item(market_hash_name="dup", display_name="已有饰品"))
    db_session.commit()
    app.dependency_overrides[get_db] = override_session(db_session)
    client = TestClient(app)

    response = client.post(
        "/api/items",
        json={
            "market_hash_name": "dup",
            "display_name": "重复饰品",
            "exterior": "",
            "category": "",
            "is_active": True,
        },
    )

    app.dependency_overrides.clear()
    assert response.status_code == 409


def test_monitor_pools_return_active_item_count(db_session):
    pool = MonitorPool(name="观察池", interval_minutes=30, description="测试")
    db_session.add(pool)
    db_session.flush()
    db_session.add(Item(market_hash_name="active", display_name="启用", pool_id=pool.id, is_active=True))
    db_session.add(Item(market_hash_name="inactive", display_name="停用", pool_id=pool.id, is_active=False))
    db_session.commit()
    app.dependency_overrides[get_db] = override_session(db_session)
    client = TestClient(app)

    response = client.get("/api/monitor-pools")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()[0]["active_item_count"] == 1


def test_monitor_pool_can_be_created_and_updated(db_session):
    db_session.add(MonitorPool(name="重点池", interval_minutes=10, description="旧"))
    db_session.commit()
    app.dependency_overrides[get_db] = override_session(db_session)
    client = TestClient(app)

    created = client.post(
        "/api/monitor-pools",
        json={"name": "事件池", "interval_minutes": 5, "description": "Major 期间"},
    )
    updated = client.put(
        f"/api/monitor-pools/{created.json()['id']}",
        json={"name": "事件高频池", "interval_minutes": 3, "description": "贴纸打折"},
    )
    duplicate_create = client.post(
        "/api/monitor-pools",
        json={"name": "重点池", "interval_minutes": 5, "description": ""},
    )
    duplicate_update = client.put(
        f"/api/monitor-pools/{created.json()['id']}",
        json={"name": "重点池", "interval_minutes": 3, "description": ""},
    )
    missing = client.put(
        "/api/monitor-pools/999",
        json={"name": "不存在", "interval_minutes": 3, "description": ""},
    )

    app.dependency_overrides.clear()
    assert created.status_code == 200
    assert created.json()["name"] == "事件池"
    assert created.json()["active_item_count"] == 0
    assert updated.status_code == 200
    assert updated.json()["name"] == "事件高频池"
    assert updated.json()["interval_minutes"] == 3
    assert duplicate_create.status_code == 409
    assert duplicate_update.status_code == 409
    assert missing.status_code == 404


def test_item_detail_returns_heatmap_and_alert_summary(db_session):
    platform = Platform(code="steam", name="Steam")
    item = Item(market_hash_name="heatmap-item", display_name="Heatmap Item")
    db_session.add_all([platform, item])
    db_session.flush()
    first = MarketSnapshot(
        item_id=item.id,
        platform_id=platform.id,
        lowest_price=100,
        sell_count=20,
        highest_buy_price=95,
        buy_count=10,
        volume_24h=5,
        avg_price_24h=98,
        captured_at=datetime(2026, 6, 5, 10, 0, 0),
    )
    second = MarketSnapshot(
        item_id=item.id,
        platform_id=platform.id,
        lowest_price=110,
        sell_count=35,
        highest_buy_price=96,
        buy_count=14,
        volume_24h=7,
        avg_price_24h=101,
        captured_at=datetime(2026, 6, 5, 10, 30, 0),
    )
    db_session.add_all([first, second])
    db_session.flush()
    db_session.add_all(
        [
            Alert(
                item_id=item.id,
                platform_id=platform.id,
                snapshot_id=second.id,
                alert_type="sell_count_change",
                title="sell changed",
                detail="sell detail",
                previous_value=20,
                current_value=35,
                absolute_change=15,
                change_rate=0.75,
                created_at=datetime(2026, 6, 5, 11, 0, 0),
            ),
            Alert(
                item_id=item.id,
                platform_id=platform.id,
                snapshot_id=second.id,
                alert_type="sell_count_change",
                title="sell changed again",
                detail="sell detail",
                previous_value=35,
                current_value=50,
                absolute_change=15,
                change_rate=0.42,
                created_at=datetime(2026, 6, 5, 12, 0, 0),
            ),
        ]
    )
    db_session.commit()
    app.dependency_overrides[get_db] = override_session(db_session)
    client = TestClient(app)

    response = client.get(f"/api/items/{item.id}")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    body = response.json()
    assert body["heatmap"][0]["hour"] == 10
    assert body["heatmap"][0]["snapshot_count"] == 2
    assert body["heatmap"][0]["max_sell_change"] == 15
    assert body["snapshots"][-1]["spread_amount"] == 14
    assert round(body["snapshots"][-1]["spread_rate"], 4) == round(14 / 110, 4)
    assert body["alert_summary"][0]["alert_type"] == "sell_count_change"
    assert len(body["alert_summary"][0]["recent_alerts"]) == 2


def test_item_history_endpoints_return_metric_series(db_session):
    platform = Platform(code="steam", name="Steam")
    item = Item(market_hash_name="history-item", display_name="History Item")
    db_session.add_all([platform, item])
    db_session.flush()
    db_session.add_all(
        [
            MarketSnapshot(
                item_id=item.id,
                platform_id=platform.id,
                lowest_price=100,
                sell_count=20,
                highest_buy_price=95,
                buy_count=10,
                volume_24h=5,
                avg_price_24h=98,
                captured_at=datetime(2026, 6, 5, 9, 0, 0),
            ),
            MarketSnapshot(
                item_id=item.id,
                platform_id=platform.id,
                lowest_price=110,
                sell_count=25,
                highest_buy_price=96,
                buy_count=12,
                volume_24h=7,
                avg_price_24h=101,
                captured_at=datetime(2026, 6, 5, 10, 0, 0),
            ),
        ]
    )
    db_session.commit()
    app.dependency_overrides[get_db] = override_session(db_session)
    client = TestClient(app)

    price = client.get(f"/api/items/{item.id}/history/price")
    sell = client.get(f"/api/items/{item.id}/history/sell", params={"limit": 1})
    buy = client.get(f"/api/items/{item.id}/history/buy")
    missing = client.get("/api/items/999/history/price")

    app.dependency_overrides.clear()
    assert price.status_code == 200
    assert [row["value"] for row in price.json()] == [100, 110]
    assert sell.status_code == 200
    assert [row["value"] for row in sell.json()] == [25]
    assert buy.status_code == 200
    assert [row["value"] for row in buy.json()] == [10, 12]
    assert missing.status_code == 404


def test_alerts_can_be_filtered(db_session):
    steam = Platform(code="steam", name="Steam")
    buff = Platform(code="buff", name="BUFF")
    target = Item(market_hash_name="target", display_name="目标饰品")
    other = Item(market_hash_name="other", display_name="其他饰品")
    db_session.add_all([steam, buff, target, other])
    db_session.flush()
    snapshot = MarketSnapshot(
        item_id=target.id,
        platform_id=steam.id,
        lowest_price=100,
        sell_count=20,
        highest_buy_price=95,
        buy_count=10,
        volume_24h=5,
        avg_price_24h=98,
    )
    other_snapshot = MarketSnapshot(
        item_id=other.id,
        platform_id=buff.id,
        lowest_price=200,
        sell_count=20,
        highest_buy_price=190,
        buy_count=10,
        volume_24h=5,
        avg_price_24h=198,
    )
    db_session.add_all([snapshot, other_snapshot])
    db_session.flush()
    db_session.add_all(
        [
            Alert(
                item_id=target.id,
                platform_id=steam.id,
                snapshot_id=snapshot.id,
                alert_type="在售变化",
                severity="P1",
                title="target",
                detail="target",
                previous_value=10,
                current_value=20,
                absolute_change=10,
                change_rate=1,
            ),
            Alert(
                item_id=other.id,
                platform_id=buff.id,
                snapshot_id=other_snapshot.id,
                alert_type="成交量异常",
                severity="P2",
                title="other",
                detail="other",
                previous_value=10,
                current_value=20,
                absolute_change=10,
                change_rate=1,
            ),
        ]
    )
    db_session.commit()
    app.dependency_overrides[get_db] = override_session(db_session)
    client = TestClient(app)

    response = client.get(
        "/api/alerts",
        params={"item": "目标", "alert_type": "在售变化", "severity": "P1", "platform": "Steam"},
    )

    app.dependency_overrides.clear()
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["item_name"] == "目标饰品"
    assert body[0]["alert_type"] == "在售变化"


def test_monitor_and_detail_return_source_quality(db_session):
    item = Item(market_hash_name="quality-item", display_name="Quality Item")
    platform = Platform(code="steam", name="Steam")
    db_session.add_all([item, platform])
    db_session.flush()
    db_session.add(
        MarketSnapshot(
            item_id=item.id,
            platform_id=platform.id,
            lowest_price=100,
            sell_count=10,
            highest_buy_price=90,
            buy_count=5,
            volume_24h=3,
            avg_price_24h=98,
            raw_payload=json.dumps(
                {
                    "source_quality": {
                        "real_fields": ["lowest_price", "volume_24h"],
                        "fallback_fields": ["sell_count", "buy_count"],
                    }
                }
            ),
        )
    )
    db_session.commit()
    app.dependency_overrides[get_db] = override_session(db_session)
    client = TestClient(app)

    monitor = client.get("/api/monitor")
    detail = client.get(f"/api/items/{item.id}")

    app.dependency_overrides.clear()
    assert monitor.status_code == 200
    assert monitor.json()[0]["source_quality"]["level"] == "partial"
    assert monitor.json()[0]["quality_penalty"] == 15
    assert monitor.json()[0]["adjusted_buy_score"] < monitor.json()[0]["buy_score"]
    assert detail.status_code == 200
    assert detail.json()["source_quality"]["real_field_count"] == 2
    assert detail.json()["decision_signal"]["action"] == "观望"
    assert detail.json()["decision_signal"]["reason"] == "参考分不足"


def test_decision_signal_returns_buy_sell_and_watch(db_session):
    platform = Platform(code="steam", name="Steam")
    buy_item = Item(market_hash_name="buy-signal", display_name="Buy Signal")
    sell_item = Item(market_hash_name="sell-signal", display_name="Sell Signal")
    watch_item = Item(market_hash_name="watch-signal", display_name="Watch Signal")
    db_session.add_all([platform, buy_item, sell_item, watch_item])
    db_session.flush()
    db_session.add_all(
        [
            MarketSnapshot(
                item_id=buy_item.id,
                platform_id=platform.id,
                lowest_price=100,
                sell_count=10,
                highest_buy_price=96,
                buy_count=5,
                volume_24h=10,
                avg_price_24h=98,
                raw_payload=json.dumps(
                    {
                        "source_quality": {
                            "real_fields": ["lowest_price", "sell_count", "highest_buy_price", "buy_count"],
                            "fallback_fields": [],
                        }
                    }
                ),
            ),
            MarketSnapshot(
                item_id=sell_item.id,
                platform_id=platform.id,
                lowest_price=100,
                sell_count=10,
                highest_buy_price=96,
                buy_count=5,
                volume_24h=10,
                avg_price_24h=98,
                raw_payload=json.dumps(
                    {
                        "source_quality": {
                            "real_fields": ["lowest_price", "sell_count", "highest_buy_price", "buy_count"],
                            "fallback_fields": [],
                        }
                    }
                ),
            ),
            MarketSnapshot(
                item_id=watch_item.id,
                platform_id=platform.id,
                lowest_price=100,
                sell_count=10,
                highest_buy_price=96,
                buy_count=5,
                volume_24h=10,
                avg_price_24h=98,
                raw_payload=json.dumps(
                    {
                        "source_quality": {
                            "real_fields": ["lowest_price"],
                            "fallback_fields": ["sell_count", "highest_buy_price", "buy_count"],
                        }
                    }
                ),
            ),
        ]
    )
    db_session.flush()
    db_session.add_all(
        [
            Alert(
                item_id=buy_item.id,
                platform_id=platform.id,
                snapshot_id=buy_item.snapshots[0].id,
                alert_type="在售变化",
                direction="偏买入机会",
                title="buy",
                detail="buy",
                previous_value=20,
                current_value=10,
                absolute_change=-10,
                change_rate=-0.5,
            ),
            Alert(
                item_id=sell_item.id,
                platform_id=platform.id,
                snapshot_id=sell_item.snapshots[0].id,
                alert_type="在售变化",
                direction="偏卖压风险",
                title="sell",
                detail="sell",
                previous_value=10,
                current_value=20,
                absolute_change=10,
                change_rate=1,
            ),
        ]
    )
    db_session.commit()
    app.dependency_overrides[get_db] = override_session(db_session)
    client = TestClient(app)

    response = client.get("/api/monitor")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    signals = {row["market_hash_name"]: row["decision_signal"] for row in response.json()}
    assert signals["buy-signal"]["action"] == "买入"
    assert signals["sell-signal"]["action"] == "卖出"
    assert signals["watch-signal"]["action"] == "观望"
    assert signals["watch-signal"]["reason"] == "数据可信度偏低"


def test_opportunities_sort_by_quality_adjusted_score(db_session):
    platform = Platform(code="steam", name="Steam")
    trusted = Item(market_hash_name="trusted", display_name="Trusted")
    fallback = Item(market_hash_name="fallback", display_name="Fallback")
    db_session.add_all([platform, trusted, fallback])
    db_session.flush()
    db_session.add_all(
        [
            MarketSnapshot(
                item_id=trusted.id,
                platform_id=platform.id,
                lowest_price=100,
                sell_count=10,
                highest_buy_price=90,
                buy_count=5,
                volume_24h=1,
                avg_price_24h=98,
                raw_payload=json.dumps(
                    {
                        "source_quality": {
                            "real_fields": ["lowest_price", "sell_count", "highest_buy_price", "buy_count"],
                            "fallback_fields": [],
                        }
                    }
                ),
            ),
            MarketSnapshot(
                item_id=fallback.id,
                platform_id=platform.id,
                lowest_price=100,
                sell_count=10,
                highest_buy_price=90,
                buy_count=5,
                volume_24h=10,
                avg_price_24h=98,
                raw_payload=json.dumps(
                    {
                        "source_quality": {
                            "real_fields": [],
                            "fallback_fields": ["lowest_price", "sell_count", "highest_buy_price", "buy_count"],
                        }
                    }
                ),
            ),
        ]
    )
    db_session.commit()
    app.dependency_overrides[get_db] = override_session(db_session)
    client = TestClient(app)

    response = client.get("/api/opportunities")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()[0]["display_name"] == "Trusted"


def test_discover_item_steam_nameid_updates_item(db_session, monkeypatch):
    item = Item(market_hash_name="AK-47 | Test", display_name="Test")
    db_session.add(item)
    db_session.commit()
    app.dependency_overrides[get_db] = override_session(db_session)
    client = TestClient(app)
    monkeypatch.setattr("app.routers.market.SteamNameIdService.discover", lambda self, market_hash_name: "12345")

    response = client.post(f"/api/items/{item.id}/steam-nameid/discover")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["steam_item_nameid"] == "12345"
    assert db_session.get(Item, item.id).steam_item_nameid == "12345"


def test_discover_item_steam_nameid_returns_bad_gateway_on_failure(db_session, monkeypatch):
    item = Item(market_hash_name="AK-47 | Test", display_name="Test")
    db_session.add(item)
    db_session.commit()
    app.dependency_overrides[get_db] = override_session(db_session)
    client = TestClient(app)

    def fail(self, market_hash_name):
        raise ValueError("not found")

    monkeypatch.setattr("app.routers.market.SteamNameIdService.discover", fail)

    response = client.post(f"/api/items/{item.id}/steam-nameid/discover")

    app.dependency_overrides.clear()
    assert response.status_code == 502


def test_validate_item_steam_nameid_returns_orderbook_metrics(db_session, monkeypatch):
    item = Item(market_hash_name="AK-47 | Test", display_name="Test", steam_item_nameid="12345")
    db_session.add(item)
    db_session.commit()
    app.dependency_overrides[get_db] = override_session(db_session)
    client = TestClient(app)
    monkeypatch.setattr(
        "app.routers.market.SteamNameIdService.validate_orderbook",
        lambda self, steam_item_nameid: {"sell_count": 8, "buy_count": 9, "highest_buy_price": 99.0},
    )

    response = client.post(f"/api/items/{item.id}/steam-nameid/validate")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert response.json()["sell_count"] == 8
    assert response.json()["buy_count"] == 9


def test_validate_item_steam_nameid_returns_error_payload(db_session, monkeypatch):
    item = Item(market_hash_name="AK-47 | Test", display_name="Test", steam_item_nameid="")
    db_session.add(item)
    db_session.commit()
    app.dependency_overrides[get_db] = override_session(db_session)
    client = TestClient(app)

    def fail(self, steam_item_nameid):
        raise ValueError("missing steam item_nameid")

    monkeypatch.setattr("app.routers.market.SteamNameIdService.validate_orderbook", fail)

    response = client.post(f"/api/items/{item.id}/steam-nameid/validate")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["ok"] is False
    assert response.json()["error"] == "missing steam item_nameid"


def test_discover_missing_steam_nameids_updates_only_active_missing_items(db_session, monkeypatch):
    missing = Item(market_hash_name="missing", display_name="Missing", is_active=True)
    existing = Item(market_hash_name="existing", display_name="Existing", steam_item_nameid="old", is_active=True)
    inactive = Item(market_hash_name="inactive", display_name="Inactive", is_active=False)
    db_session.add_all([missing, existing, inactive])
    db_session.commit()
    app.dependency_overrides[get_db] = override_session(db_session)
    client = TestClient(app)
    monkeypatch.setattr("app.routers.market.SteamNameIdService.discover", lambda self, market_hash_name: f"id-{market_hash_name}")

    response = client.post("/api/steam-nameids/discover-missing")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["success_count"] == 1
    assert db_session.get(Item, missing.id).steam_item_nameid == "id-missing"
    assert db_session.get(Item, existing.id).steam_item_nameid == "old"
    assert db_session.get(Item, inactive.id).steam_item_nameid == ""


def test_validate_all_steam_nameids_returns_batch_result(db_session, monkeypatch):
    ready = Item(market_hash_name="ready", display_name="Ready", steam_item_nameid="123", is_active=True)
    missing = Item(market_hash_name="missing", display_name="Missing", steam_item_nameid="", is_active=True)
    db_session.add_all([ready, missing])
    db_session.commit()
    app.dependency_overrides[get_db] = override_session(db_session)
    client = TestClient(app)
    monkeypatch.setattr(
        "app.routers.market.SteamNameIdService.validate_orderbook",
        lambda self, steam_item_nameid: {"sell_count": 8, "buy_count": 9, "highest_buy_price": 99.0},
    )

    response = client.post("/api/steam-nameids/validate-all")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["success_count"] == 1
    assert response.json()["results"][0]["market_hash_name"] == "ready"
