import json
from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app
from app.models import Alert, CollectRunLog, Item, MarketSnapshot, Platform, PushRecord
from tests.test_strategy_api import override_session


def test_ops_health_returns_ok_metrics(db_session):
    alert = create_ops_fixture(db_session)
    db_session.add(
        PushRecord(
            alert_id=alert.id,
            channel="none",
            status="skipped",
            target="",
            message="ok",
        )
    )
    db_session.add(
        CollectRunLog(
            mode="worker",
            provider="mock",
            status="success",
            item_count=2,
            snapshot_count=2,
            alert_count=1,
            error_count=0,
            real_field_count=8,
            fallback_field_count=2,
            fallback_count=0,
            duration_ms=120,
            started_at=datetime.utcnow() - timedelta(minutes=5),
            finished_at=datetime.utcnow() - timedelta(minutes=4),
        )
    )
    db_session.commit()
    app.dependency_overrides[get_db] = override_session(db_session)
    client = TestClient(app)

    response = client.get("/api/ops/health")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["latest_run_status"] == "success"
    assert body["collect_success_rate"] == 1
    assert body["push_success_rate"] == 1
    assert body["snapshot_count_24h"] == 2
    assert body["alert_count_24h"] == 1
    assert body["real_field_ratio_24h"] == 0.8


def test_ops_health_warns_without_recent_runs(db_session):
    app.dependency_overrides[get_db] = override_session(db_session)
    client = TestClient(app)

    response = client.get("/api/ops/health")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["status"] == "warn"
    assert response.json()["latest_run_status"] == "none"


def test_ops_health_fails_when_recent_runs_all_failed(db_session):
    db_session.add(
        CollectRunLog(
            mode="worker",
            provider="mock",
            status="failed",
            item_count=1,
            snapshot_count=0,
            alert_count=0,
            error_count=1,
            started_at=datetime.utcnow() - timedelta(minutes=3),
            finished_at=datetime.utcnow() - timedelta(minutes=2),
        )
    )
    db_session.commit()
    app.dependency_overrides[get_db] = override_session(db_session)
    client = TestClient(app)

    response = client.get("/api/ops/health")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["status"] == "fail"


def test_ops_readiness_reports_empty_state(db_session):
    app.dependency_overrides[get_db] = override_session(db_session)
    client = TestClient(app)

    response = client.get("/api/ops/readiness")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    body = response.json()
    assert body["ready_for_7d_review"] is False
    assert body["collect_run_count"] == 0
    assert body["monitored_item_count"] == 0


def test_ops_readiness_marks_seven_day_collection_ready(db_session):
    platform = Platform(code="steam", name="Steam")
    first_item = Item(market_hash_name="ready-1", display_name="Ready 1")
    second_item = Item(market_hash_name="ready-2", display_name="Ready 2")
    db_session.add_all([platform, first_item, second_item])
    db_session.flush()
    start = datetime.utcnow() - timedelta(days=8)
    for index in range(9):
        db_session.add(
            CollectRunLog(
                mode="worker",
                provider="mock",
                status="success",
                item_count=2,
                snapshot_count=2,
                started_at=start + timedelta(days=index),
                finished_at=start + timedelta(days=index, minutes=1),
            )
        )
    for item in [first_item, second_item]:
        db_session.add(
            MarketSnapshot(
                item_id=item.id,
                platform_id=platform.id,
                lowest_price=100,
                sell_count=10,
                highest_buy_price=90,
                buy_count=5,
                volume_24h=2,
                avg_price_24h=98,
            )
        )
    db_session.commit()
    app.dependency_overrides[get_db] = override_session(db_session)
    client = TestClient(app)

    response = client.get("/api/ops/readiness")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    body = response.json()
    assert body["ready_for_7d_review"] is True
    assert body["observed_days"] >= 7
    assert body["collect_run_count"] == 9
    assert body["collect_success_rate"] == 1
    assert body["snapshot_coverage_rate"] == 1


def test_source_field_quality_counts_real_and_fallback_fields(db_session):
    platform = Platform(code="steam", name="Steam")
    item = Item(market_hash_name="field-quality", display_name="Field Quality")
    db_session.add_all([platform, item])
    db_session.flush()
    first_payload = {
        "source_quality": {
            "real_fields": ["lowest_price", "volume_24h", "avg_price_24h"],
            "fallback_fields": ["sell_count", "highest_buy_price", "buy_count"],
        }
    }
    second_payload = {
        "source_quality": {
            "real_fields": ["sell_count", "highest_buy_price", "buy_count"],
            "fallback_fields": ["lowest_price", "volume_24h", "avg_price_24h"],
        }
    }
    for raw_payload in [first_payload, second_payload, {}]:
        db_session.add(
            MarketSnapshot(
                item_id=item.id,
                platform_id=platform.id,
                lowest_price=100,
                sell_count=10,
                highest_buy_price=90,
                buy_count=5,
                volume_24h=2,
                avg_price_24h=98,
                raw_payload=json.dumps(raw_payload),
            )
        )
    db_session.commit()
    app.dependency_overrides[get_db] = override_session(db_session)
    client = TestClient(app)

    response = client.get("/api/source/field-quality")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    body = response.json()
    fields = {field["field"]: field for field in body["fields"]}
    assert body["snapshot_sample_count"] == 3
    assert fields["lowest_price"]["real_count"] == 1
    assert fields["lowest_price"]["fallback_count"] == 2
    assert fields["sell_count"]["real_count"] == 1
    assert fields["sell_count"]["fallback_count"] == 2
    assert fields["volume_24h"]["real_ratio"] == 1 / 3


def create_ops_fixture(db_session) -> Alert:
    item = Item(market_hash_name="ops-item", display_name="Ops Item")
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
    alert = Alert(
        item_id=item.id,
        platform_id=platform.id,
        snapshot_id=snapshot.id,
        alert_type="在售变化",
        title="ops",
        detail="ops",
        previous_value=10,
        current_value=20,
        absolute_change=10,
        change_rate=1,
    )
    db_session.add(alert)
    db_session.flush()
    return alert
