from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app
from app.models import Alert, Item, MarketSnapshot, Platform
from tests.test_strategy_api import override_session


def test_alert_coverage_reports_type_and_traceable_counts(db_session):
    item = Item(market_hash_name="coverage-item", display_name="Coverage Item")
    platform = Platform(code="steam", name="Steam")
    db_session.add_all([item, platform])
    db_session.flush()
    snapshot = MarketSnapshot(
        item_id=item.id,
        platform_id=platform.id,
        lowest_price=100,
        sell_count=10,
        highest_buy_price=90,
        buy_count=5,
        volume_24h=2,
        avg_price_24h=98,
    )
    db_session.add(snapshot)
    db_session.flush()
    db_session.add_all(
        [
            Alert(
                item_id=item.id,
                platform_id=platform.id,
                snapshot_id=snapshot.id,
                alert_type="在售变化",
                title="sell",
                detail="sell",
                previous_value=10,
                current_value=20,
                absolute_change=10,
                change_rate=1,
                created_at=datetime.utcnow() - timedelta(hours=1),
            ),
            Alert(
                item_id=item.id,
                platform_id=platform.id,
                snapshot_id=999,
                alert_type="底价变化",
                title="price",
                detail="price",
                previous_value=100,
                current_value=90,
                absolute_change=-10,
                change_rate=-0.1,
                created_at=datetime.utcnow() - timedelta(days=2),
            ),
        ]
    )
    db_session.commit()
    app.dependency_overrides[get_db] = override_session(db_session)
    client = TestClient(app)

    response = client.get("/api/alerts/coverage")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    body = response.json()
    types = {row["alert_type"]: row for row in body["types"]}
    assert body["total_count"] == 2
    assert body["recent_24h_count"] == 1
    assert body["covered_type_count"] == 2
    assert body["expected_type_count"] == 5
    assert body["traceable_count"] == 1
    assert body["traceable_rate"] == 0.5
    assert body["latest_alert"]["alert_type"] == "在售变化"
    assert types["在售变化"]["count"] == 1
    assert types["底价变化"]["count"] == 1
    assert types["成交量异常"]["count"] == 0
