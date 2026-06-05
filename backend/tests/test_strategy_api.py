from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app
from app.models import StrategyConfig


def override_session(db_session):
    def dependency():
        yield db_session

    return dependency


def test_strategy_can_be_read_and_updated(db_session):
    db_session.add(StrategyConfig(name="default"))
    db_session.commit()
    app.dependency_overrides[get_db] = override_session(db_session)
    client = TestClient(app)

    current = client.get("/api/strategy")
    updated = client.put(
        "/api/strategy",
        json={
            "min_absolute_sell_change": 45,
            "min_sell_change_rate": 0.18,
            "min_price_change_rate": 0.04,
            "min_buy_change_rate": 0.16,
            "cooldown_minutes": 30,
        },
    )

    app.dependency_overrides.clear()
    assert current.status_code == 200
    assert updated.status_code == 200
    assert updated.json()["min_absolute_sell_change"] == 45
    assert updated.json()["cooldown_minutes"] == 30


def test_strategy_rejects_invalid_threshold(db_session):
    db_session.add(StrategyConfig(name="default"))
    db_session.commit()
    app.dependency_overrides[get_db] = override_session(db_session)
    client = TestClient(app)

    response = client.put(
        "/api/strategy",
        json={
            "min_absolute_sell_change": 0,
            "min_sell_change_rate": 0.18,
            "min_price_change_rate": 0.04,
            "min_buy_change_rate": 0.16,
            "cooldown_minutes": 30,
        },
    )

    app.dependency_overrides.clear()
    assert response.status_code == 422
