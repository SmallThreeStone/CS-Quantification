from fastapi.testclient import TestClient
import json

from app.database import get_db
from app.main import app
from app.models import Item, MarketSnapshot, Platform, StrategyConfig


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
            "min_price_volatility_rate": 0.09,
            "min_buy_change_rate": 0.16,
            "min_volume_change_rate": 0.7,
            "cooldown_minutes": 30,
            "quality_penalty_max": 40,
            "sell_fee_rate": 0.1,
            "withdraw_fee_rate": 0.02,
            "fx_rate": 1.1,
        },
    )

    app.dependency_overrides.clear()
    assert current.status_code == 200
    assert updated.status_code == 200
    assert updated.json()["min_absolute_sell_change"] == 45
    assert updated.json()["cooldown_minutes"] == 30
    assert updated.json()["min_price_volatility_rate"] == 0.09
    assert updated.json()["min_volume_change_rate"] == 0.7
    assert updated.json()["quality_penalty_max"] == 40
    assert updated.json()["sell_fee_rate"] == 0.1
    assert updated.json()["withdraw_fee_rate"] == 0.02
    assert updated.json()["fx_rate"] == 1.1


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
            "min_price_volatility_rate": 0.08,
            "min_buy_change_rate": 0.16,
            "min_volume_change_rate": 0.5,
            "cooldown_minutes": 30,
            "quality_penalty_max": 30,
            "sell_fee_rate": 0.13,
            "withdraw_fee_rate": 0,
            "fx_rate": 1,
        },
    )

    app.dependency_overrides.clear()
    assert response.status_code == 422


def test_strategy_quality_penalty_changes_adjusted_scores(db_session):
    platform = Platform(code="steam", name="Steam")
    item = Item(market_hash_name="quality-score", display_name="Quality Score")
    db_session.add_all([platform, item, StrategyConfig(name="default", quality_penalty_max=60)])
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

    response = client.get("/api/monitor")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    row = response.json()[0]
    assert row["quality_penalty"] == 30
    assert row["adjusted_buy_score"] == max(0, row["buy_score"] - 30)


def test_strategy_fee_rates_change_net_spread_metrics(db_session):
    platform = Platform(code="steam", name="Steam")
    item = Item(market_hash_name="fee-score", display_name="Fee Score")
    db_session.add_all(
        [
            platform,
            item,
            StrategyConfig(name="default", sell_fee_rate=0.1, withdraw_fee_rate=0.02, fx_rate=1.1),
        ]
    )
    db_session.flush()
    db_session.add(
        MarketSnapshot(
            item_id=item.id,
            platform_id=platform.id,
            lowest_price=100,
            sell_count=10,
            highest_buy_price=80,
            buy_count=5,
            volume_24h=3,
            avg_price_24h=98,
        )
    )
    db_session.commit()
    app.dependency_overrides[get_db] = override_session(db_session)
    client = TestClient(app)

    response = client.get("/api/monitor")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    snapshot = response.json()[0]["latest_snapshot"]
    assert round(snapshot["net_sell_price"], 2) == 96.8
    assert round(snapshot["net_spread_amount"], 2) == 16.8
    assert round(snapshot["net_spread_rate"], 4) == 0.168


def test_category_strategy_adjusts_scores_and_explains_profile(db_session):
    platform = Platform(code="steam", name="Steam")
    item = Item(market_hash_name="gloves-score", display_name="Gloves Score", category="gloves")
    db_session.add_all([platform, item, StrategyConfig(name="default")])
    db_session.flush()
    db_session.add(
        MarketSnapshot(
            item_id=item.id,
            platform_id=platform.id,
            lowest_price=100,
            sell_count=10,
            highest_buy_price=80,
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
        )
    )
    db_session.commit()
    app.dependency_overrides[get_db] = override_session(db_session)
    client = TestClient(app)

    response = client.get("/api/monitor")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    row = response.json()[0]
    assert row["category_strategy"]["profile"] == "高客单低流动"
    assert row["category_strategy"]["buy_adjustment"] == -13
    assert row["category_strategy"]["sell_adjustment"] == 8
    assert row["adjusted_buy_score"] == row["buy_score"] - 13
    assert row["adjusted_sell_score"] == row["sell_score"] + 8
