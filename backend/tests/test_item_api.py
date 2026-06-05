from fastapi.testclient import TestClient
from datetime import datetime

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
    assert body["alert_summary"][0]["alert_type"] == "sell_count_change"
    assert len(body["alert_summary"][0]["recent_alerts"]) == 2


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
