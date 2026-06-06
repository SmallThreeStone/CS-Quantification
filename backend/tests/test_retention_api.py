from datetime import datetime, timedelta

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


def test_retention_cleanup_deletes_expired_rows_but_keeps_alert_snapshots(db_session):
    item = Item(market_hash_name="cleanup-item", display_name="Cleanup Item")
    platform = Platform(code="steam", name="Steam")
    db_session.add_all([item, platform])
    db_session.flush()
    old_at = datetime.utcnow() - timedelta(days=181)
    recent_at = datetime.utcnow() - timedelta(days=10)
    referenced_snapshot = MarketSnapshot(
        item_id=item.id,
        platform_id=platform.id,
        lowest_price=100,
        sell_count=10,
        highest_buy_price=90,
        buy_count=5,
        volume_24h=2,
        avg_price_24h=98,
        captured_at=old_at,
    )
    expired_snapshot = MarketSnapshot(
        item_id=item.id,
        platform_id=platform.id,
        lowest_price=101,
        sell_count=9,
        highest_buy_price=91,
        buy_count=4,
        volume_24h=3,
        avg_price_24h=99,
        captured_at=old_at,
    )
    recent_snapshot = MarketSnapshot(
        item_id=item.id,
        platform_id=platform.id,
        lowest_price=102,
        sell_count=8,
        highest_buy_price=92,
        buy_count=3,
        volume_24h=4,
        avg_price_24h=100,
        captured_at=recent_at,
    )
    db_session.add_all([referenced_snapshot, expired_snapshot, recent_snapshot])
    db_session.flush()
    db_session.add(
        Alert(
            item_id=item.id,
            platform_id=platform.id,
            snapshot_id=referenced_snapshot.id,
            alert_type="在售变化",
            title="cleanup",
            detail="cleanup",
            previous_value=10,
            current_value=20,
            absolute_change=10,
            change_rate=1,
            created_at=old_at,
        )
    )
    db_session.add_all(
        [
            CollectRunLog(mode="worker", provider="mock", status="success", started_at=datetime.utcnow() - timedelta(days=91)),
            CollectRunLog(mode="worker", provider="mock", status="success", started_at=recent_at),
        ]
    )
    db_session.commit()
    app.dependency_overrides[get_db] = override_session(db_session)
    client = TestClient(app)

    response = client.post("/api/retention/cleanup")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    body = response.json()
    assert body["deleted_snapshots"] == 1
    assert body["deleted_collect_logs"] == 1
    remaining_snapshot_ids = {row.id for row in db_session.query(MarketSnapshot).all()}
    assert remaining_snapshot_ids == {referenced_snapshot.id, recent_snapshot.id}
    assert db_session.query(CollectRunLog).count() == 1
