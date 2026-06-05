from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app
from app.models import Item
from tests.test_strategy_api import override_session


def test_item_can_be_created_and_deactivated(db_session):
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
        },
    )
    inactive = client.patch(f"/api/items/{created.json()['id']}/active", params={"is_active": False})
    monitor = client.get("/api/monitor")

    app.dependency_overrides.clear()
    assert created.status_code == 200
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
