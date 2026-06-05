from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app
from app.models import Item, MonitorPool
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
            "is_active": True,
            "pool_id": pool.id,
        },
    )
    inactive = client.patch(f"/api/items/{created.json()['id']}/active", params={"is_active": False})
    monitor = client.get("/api/monitor")

    app.dependency_overrides.clear()
    assert created.status_code == 200
    assert created.json()["pool_name"] == "重点池"
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
