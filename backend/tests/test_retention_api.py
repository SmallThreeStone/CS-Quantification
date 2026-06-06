from datetime import datetime

from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app
from app.models import Alert, BacktestResult, CollectRunLog, Item, MarketSnapshot, Platform
from tests.test_strategy_api import override_session


def test_retention_returns_policy_and_metric_counts(db_session):
    item = Item(market_hash_name="retention-item", display_name="Retention Item")
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
        captured_at=datetime(2026, 1, 1, 10, 0),
    )
    db_session.add(snapshot)
    db_session.flush()
    alert = Alert(
        item_id=item.id,
        platform_id=platform.id,
        snapshot_id=snapshot.id,
        alert_type="在售变化",
        title="retention",
        detail="retention",
        previous_value=10,
        current_value=20,
        absolute_change=10,
        change_rate=1,
        created_at=datetime(2026, 1, 1, 10, 5),
    )
    db_session.add(alert)
    db_session.flush()
    db_session.add(
        BacktestResult(
            alert_id=alert.id,
            item_id=item.id,
            platform_id=platform.id,
            horizon_minutes=60,
            entry_price=100,
            exit_price=110,
            price_change=10,
            change_rate=0.1,
            evaluated_at=datetime(2026, 1, 1, 11, 0),
            created_at=datetime(2026, 1, 1, 11, 1),
        )
    )
    db_session.add(
        CollectRunLog(
            mode="worker",
            provider="mock",
            status="success",
            snapshot_count=1,
            started_at=datetime(2026, 1, 1, 9, 55),
        )
    )
    db_session.commit()
    app.dependency_overrides[get_db] = override_session(db_session)
    client = TestClient(app)

    response = client.get("/api/retention")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    body = response.json()
    assert body["snapshot_retention_days"] == 180
    assert body["alert_retention_days"] is None
    metrics = {row["name"]: row for row in body["metrics"]}
    assert metrics["行情快照"]["row_count"] == 1
    assert metrics["告警记录"]["retention_days"] is None
    assert metrics["回测结果"]["policy"] == "长期保留，用于策略调参"
    assert metrics["采集日志"]["retention_days"] == 90
