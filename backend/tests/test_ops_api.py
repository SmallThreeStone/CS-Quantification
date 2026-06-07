import json
from datetime import datetime, timedelta
from pathlib import Path

from fastapi.testclient import TestClient
import app.routers.market as market_router

from app.config import settings
from app.database import get_db
from app.main import app
from app.models import Alert, BacktestResult, CollectRunLog, Item, MarketSnapshot, Platform, PushRecord, StrategyConfig
from app.services.api_metrics import api_metrics_store
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


def test_ops_api_latency_reports_empty_window(db_session):
    api_metrics_store.clear()
    app.dependency_overrides[get_db] = override_session(db_session)
    client = TestClient(app)

    response = client.get("/api/ops/api-latency")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "warn"
    assert body["request_count"] == 0
    assert body["latest_path"] is None


def test_ops_api_latency_reports_recent_samples(db_session):
    api_metrics_store.clear()
    api_metrics_store.record("/api/health", "GET", 200, 10)
    api_metrics_store.record("/api/monitor", "GET", 200, 20)
    app.dependency_overrides[get_db] = override_session(db_session)
    client = TestClient(app)

    response = client.get("/api/ops/api-latency")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["request_count"] >= 2
    assert body["avg_latency_ms"] >= 10
    assert body["p95_latency_ms"] >= 20
    assert body["max_latency_ms"] >= 20
    assert body["slow_request_count"] == 0
    assert body["error_count"] == 0


def test_ops_api_latency_flags_slow_and_error_samples(db_session):
    api_metrics_store.clear()
    api_metrics_store.record("/api/slow", "GET", 200, 1200)
    api_metrics_store.record("/api/error", "GET", 500, 30)
    app.dependency_overrides[get_db] = override_session(db_session)
    client = TestClient(app)

    response = client.get("/api/ops/api-latency")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "fail"
    assert body["slow_request_count"] >= 1
    assert body["error_count"] >= 1


def test_ops_runtime_reports_safe_runtime_config(db_session):
    previous_database_url = settings.database_url
    previous_provider = settings.market_provider
    previous_orderbook = settings.steam_orderbook_enabled
    previous_worker_sleep = settings.worker_sleep_seconds
    previous_push_channel = settings.push_channel
    previous_wechat = settings.wechat_webhook_url
    previous_cors = settings.cors_origins
    settings.database_url = "postgresql+psycopg://user:secret@db/cs"
    settings.market_provider = "steam"
    settings.steam_orderbook_enabled = True
    settings.worker_sleep_seconds = 45
    settings.push_channel = "wechat"
    settings.wechat_webhook_url = "https://example.test/webhook"
    settings.cors_origins = "http://localhost:5173,https://cs.example.test"
    app.dependency_overrides[get_db] = override_session(db_session)
    client = TestClient(app)
    try:
        response = client.get("/api/ops/runtime")
    finally:
        settings.database_url = previous_database_url
        settings.market_provider = previous_provider
        settings.steam_orderbook_enabled = previous_orderbook
        settings.worker_sleep_seconds = previous_worker_sleep
        settings.push_channel = previous_push_channel
        settings.wechat_webhook_url = previous_wechat
        settings.cors_origins = previous_cors
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["version"] == "0.1.69"
    assert body["database_kind"] == "postgresql"
    assert body["market_provider"] == "steam"
    assert body["steam_orderbook_enabled"] is True
    assert body["worker_sleep_seconds"] == 45
    assert body["push_channel"] == "wechat"
    assert body["push_configured"] is True
    assert body["cors_origin_count"] == 2
    assert "secret" not in json.dumps(body)


def test_ops_runtime_marks_none_push_as_unconfigured(db_session):
    previous_push_channel = settings.push_channel
    settings.push_channel = "none"
    app.dependency_overrides[get_db] = override_session(db_session)
    client = TestClient(app)
    try:
        response = client.get("/api/ops/runtime")
    finally:
        settings.push_channel = previous_push_channel
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["push_configured"] is False


def test_ops_runtime_audit_flags_default_deploy_risks(db_session):
    previous_database_url = settings.database_url
    previous_provider = settings.market_provider
    previous_orderbook = settings.steam_orderbook_enabled
    previous_worker_sleep = settings.worker_sleep_seconds
    previous_push_channel = settings.push_channel
    previous_cors = settings.cors_origins
    settings.database_url = "postgresql://cs_quant:cs_quant_password@postgres:5432/cs_quant"
    settings.market_provider = "mock"
    settings.steam_orderbook_enabled = False
    settings.worker_sleep_seconds = 600
    settings.push_channel = "none"
    settings.cors_origins = "http://localhost,http://127.0.0.1:5173"
    app.dependency_overrides[get_db] = override_session(db_session)
    client = TestClient(app)
    try:
        response = client.get("/api/ops/runtime-audit")
    finally:
        settings.database_url = previous_database_url
        settings.market_provider = previous_provider
        settings.steam_orderbook_enabled = previous_orderbook
        settings.worker_sleep_seconds = previous_worker_sleep
        settings.push_channel = previous_push_channel
        settings.cors_origins = previous_cors
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    items = {item["key"]: item for item in body["items"]}
    assert body["status"] == "fail"
    assert items["postgres_password"]["status"] == "fail"
    assert items["market_provider"]["status"] == "warn"
    assert items["orderbook"]["status"] == "warn"
    assert items["push"]["status"] == "warn"
    assert items["worker_sleep"]["status"] == "warn"
    assert items["cors"]["status"] == "warn"


def test_ops_runtime_audit_marks_production_shape_ready(db_session):
    previous_database_url = settings.database_url
    previous_provider = settings.market_provider
    previous_orderbook = settings.steam_orderbook_enabled
    previous_worker_sleep = settings.worker_sleep_seconds
    previous_push_channel = settings.push_channel
    previous_wechat = settings.wechat_webhook_url
    previous_cors = settings.cors_origins
    settings.database_url = "postgresql://cs_quant:strong_password@postgres:5432/cs_quant"
    settings.market_provider = "steam"
    settings.steam_orderbook_enabled = True
    settings.worker_sleep_seconds = 30
    settings.push_channel = "wechat"
    settings.wechat_webhook_url = "https://example.test/webhook"
    settings.cors_origins = "https://cs.example.test"
    app.dependency_overrides[get_db] = override_session(db_session)
    client = TestClient(app)
    try:
        response = client.get("/api/ops/runtime-audit")
    finally:
        settings.database_url = previous_database_url
        settings.market_provider = previous_provider
        settings.steam_orderbook_enabled = previous_orderbook
        settings.worker_sleep_seconds = previous_worker_sleep
        settings.push_channel = previous_push_channel
        settings.wechat_webhook_url = previous_wechat
        settings.cors_origins = previous_cors
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["fail_count"] == 0
    assert body["warn_count"] == 0


def test_ops_mvp_scope_reports_review_for_empty_state(db_session):
    app.dependency_overrides[get_db] = override_session(db_session)
    client = TestClient(app)

    response = client.get("/api/ops/mvp-scope")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    body = response.json()
    items = {item["key"]: item for item in body["items"]}
    assert body["status"] == "review"
    assert body["item_count"] == 6
    assert body["review_count"] >= 1
    assert items["monitor_overview"]["status"] == "review"
    assert items["push_module"]["status"] == "review"


def test_ops_mvp_scope_marks_core_panels_ready(db_session):
    alert = create_ops_fixture(db_session)
    db_session.add(StrategyConfig(name="default"))
    db_session.add(
        PushRecord(
            alert_id=alert.id,
            channel="wechat",
            status="sent",
            target="wechat",
            message="ok",
            sent_at=datetime.utcnow(),
        )
    )
    db_session.commit()
    app.dependency_overrides[get_db] = override_session(db_session)
    client = TestClient(app)

    response = client.get("/api/ops/mvp-scope")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    body = response.json()
    items = {item["key"]: item for item in body["items"]}
    assert body["status"] == "ready"
    assert body["ready_count"] == 6
    assert items["monitor_overview"]["status"] == "ready"
    assert items["item_detail"]["status"] == "ready"
    assert items["alert_center"]["status"] == "ready"
    assert items["push_module"]["status"] == "ready"


def test_ops_db_write_volume_reports_idle_empty_state(db_session):
    app.dependency_overrides[get_db] = override_session(db_session)
    client = TestClient(app)

    response = client.get("/api/ops/db-write-volume")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "idle"
    assert body["window_hours"] == 24
    assert body["total_recent_24h_count"] == 0
    assert body["total_row_count"] == 0
    assert body["latest_write_at"] is None
    assert {metric["table"] for metric in body["metrics"]} == {
        "market_snapshots",
        "alerts",
        "push_records",
        "backtest_results",
        "collect_run_logs",
    }


def test_ops_db_write_volume_reports_recent_writes(db_session):
    alert = create_ops_fixture(db_session)
    db_session.add(
        PushRecord(
            alert_id=alert.id,
            channel="wechat",
            status="sent",
            target="wechat",
            message="ok",
        )
    )
    db_session.add(
        CollectRunLog(
            mode="worker",
            provider="mock",
            status="success",
            item_count=1,
            snapshot_count=1,
            alert_count=1,
            started_at=datetime.utcnow() - timedelta(minutes=5),
        )
    )
    db_session.commit()
    app.dependency_overrides[get_db] = override_session(db_session)
    client = TestClient(app)

    response = client.get("/api/ops/db-write-volume")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    body = response.json()
    metrics = {metric["table"]: metric for metric in body["metrics"]}
    assert body["status"] == "active"
    assert body["total_recent_24h_count"] >= 4
    assert body["total_row_count"] >= 4
    assert body["latest_write_at"] is not None
    assert metrics["market_snapshots"]["recent_24h_count"] == 1
    assert metrics["alerts"]["recent_24h_count"] == 1
    assert metrics["push_records"]["recent_24h_count"] == 1
    assert metrics["collect_run_logs"]["recent_24h_count"] == 1


def test_ops_host_resources_reports_current_host_state(db_session):
    app.dependency_overrides[get_db] = override_session(db_session)
    client = TestClient(app)

    response = client.get("/api/ops/host-resources")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {"ok", "warn", "fail"}
    assert body["checked_at"] is not None
    assert body["disk_total_gb"] is None or body["disk_total_gb"] > 0
    assert body["disk_used_gb"] is None or body["disk_used_gb"] >= 0
    assert body["disk_percent"] is None or 0 <= body["disk_percent"] <= 100
    assert body["memory_percent"] is None or 0 <= body["memory_percent"] <= 100
    assert body["cpu_percent"] is None or 0 <= body["cpu_percent"] <= 100


def test_ops_backups_warns_without_backup_files(db_session, tmp_path, monkeypatch):
    create_backup_scripts(tmp_path)
    monkeypatch.setattr(market_router, "_project_root", lambda: tmp_path)
    app.dependency_overrides[get_db] = override_session(db_session)
    client = TestClient(app)

    response = client.get("/api/ops/backups")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "warn"
    assert {metric["key"] for metric in body["metrics"]} == {"postgres", "config"}
    assert body["cron"]["status"] == "warn"
    assert body["cron"]["cron_exists"] is False
    for metric in body["metrics"]:
        assert metric["script_exists"] is True
        assert metric["file_count"] == 0
        assert metric["latest_file"] is None


def test_ops_backups_reports_ready_with_recent_non_empty_files(db_session, tmp_path, monkeypatch):
    create_backup_scripts(tmp_path)
    create_backup_cron(tmp_path)
    postgres_dir = tmp_path / "backups" / "postgres"
    config_dir = tmp_path / "backups" / "config"
    postgres_dir.mkdir(parents=True)
    config_dir.mkdir(parents=True)
    (postgres_dir / "cs_quant_20260607_120000.dump").write_bytes(b"postgres")
    (config_dir / "config_20260607_120000.zip").write_bytes(b"config")
    monkeypatch.setattr(market_router, "_project_root", lambda: tmp_path)
    app.dependency_overrides[get_db] = override_session(db_session)
    client = TestClient(app)

    response = client.get("/api/ops/backups")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["cron"]["status"] == "ready"
    assert body["cron"]["postgres_job_installed"] is True
    assert body["cron"]["config_job_installed"] is True
    metrics = {metric["key"]: metric for metric in body["metrics"]}
    assert metrics["postgres"]["latest_file"].endswith(".dump")
    assert metrics["postgres"]["latest_size_bytes"] > 0
    assert metrics["config"]["latest_file"].endswith(".zip")
    assert metrics["config"]["latest_size_bytes"] > 0


def test_ops_acceptance_reports_review_for_empty_state(db_session):
    app.dependency_overrides[get_db] = override_session(db_session)
    client = TestClient(app)

    response = client.get("/api/ops/acceptance")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    body = response.json()
    items = {item["key"]: item for item in body["items"]}
    assert body["status"] in {"review", "blocked"}
    assert items["stable_collection_7d"]["status"] == "review"
    assert items["decision_reference_only"]["status"] == "passed"
    assert "观察 0.0 天" in items["stable_collection_7d"]["evidence"]


def test_ops_acceptance_marks_core_evidence_passed(db_session):
    previous_database_url = settings.database_url
    previous_provider = settings.market_provider
    previous_orderbook = settings.steam_orderbook_enabled
    previous_worker_sleep = settings.worker_sleep_seconds
    previous_push_channel = settings.push_channel
    previous_wechat = settings.wechat_webhook_url
    previous_cors = settings.cors_origins
    settings.database_url = "postgresql://cs_quant:strong_password@postgres:5432/cs_quant"
    settings.market_provider = "steam"
    settings.steam_orderbook_enabled = True
    settings.worker_sleep_seconds = 30
    settings.push_channel = "wechat"
    settings.wechat_webhook_url = "https://example.test/webhook"
    settings.cors_origins = "https://cs.example.test"
    platform = Platform(code="steam", name="Steam")
    item = Item(market_hash_name="accept-item", display_name="Accept Item", steam_item_nameid="123", is_active=True)
    db_session.add_all([platform, item, StrategyConfig(name="default")])
    db_session.flush()
    start = datetime.utcnow() - timedelta(days=8)
    for index in range(9):
        db_session.add(
            CollectRunLog(
                mode="worker",
                provider="steam",
                status="success",
                item_count=1,
                snapshot_count=1,
                started_at=start + timedelta(days=index),
                finished_at=start + timedelta(days=index, minutes=1),
            )
        )
    snapshot = MarketSnapshot(
        item_id=item.id,
        platform_id=platform.id,
        lowest_price=100,
        sell_count=10,
        highest_buy_price=90,
        buy_count=5,
        volume_24h=2,
        avg_price_24h=98,
        raw_payload=json.dumps(
            {
                "source_quality": {
                    "real_fields": ["lowest_price", "sell_count", "highest_buy_price", "buy_count", "volume_24h", "avg_price_24h"],
                    "fallback_fields": [],
                }
            }
        ),
    )
    db_session.add(snapshot)
    db_session.flush()
    alert = Alert(
        item_id=item.id,
        platform_id=platform.id,
        snapshot_id=snapshot.id,
        alert_type="在售变化",
        title="accept",
        detail="accept",
        previous_value=10,
        current_value=20,
        absolute_change=10,
        change_rate=1,
    )
    db_session.add(alert)
    db_session.flush()
    db_session.add_all(
        [
            PushRecord(alert_id=alert.id, channel="wechat", status="sent", target="", message="ok"),
            BacktestResult(
                alert_id=alert.id,
                item_id=item.id,
                platform_id=platform.id,
                horizon_minutes=60,
                entry_price=100,
                exit_price=105,
                price_change=5,
                change_rate=0.05,
                evaluated_at=datetime.utcnow(),
            ),
        ]
    )
    db_session.commit()
    app.dependency_overrides[get_db] = override_session(db_session)
    client = TestClient(app)
    try:
        response = client.get("/api/ops/acceptance")
    finally:
        settings.database_url = previous_database_url
        settings.market_provider = previous_provider
        settings.steam_orderbook_enabled = previous_orderbook
        settings.worker_sleep_seconds = previous_worker_sleep
        settings.push_channel = previous_push_channel
        settings.wechat_webhook_url = previous_wechat
        settings.cors_origins = previous_cors
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    items = {item["key"]: item for item in body["items"]}
    assert body["blocked_count"] == 0
    assert items["stable_collection_7d"]["status"] == "passed"
    assert items["sell_depth_accuracy"]["status"] == "passed"
    assert items["buy_depth_accuracy"]["status"] == "passed"
    assert items["alert_traceability"]["status"] == "passed"
    assert items["opportunity_ranking"]["status"] == "passed"


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


def test_source_config_reports_mock_suggestion(db_session):
    previous_provider = settings.market_provider
    settings.market_provider = "mock"
    app.dependency_overrides[get_db] = override_session(db_session)
    client = TestClient(app)
    try:
        response = client.get("/api/source/config")
    finally:
        settings.market_provider = previous_provider
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "mock"
    assert body["readiness"] == "mock"
    assert "Mock 数据源" in body["suggestion"]


def test_source_config_reports_orderbook_nameid_coverage(db_session):
    previous_provider = settings.market_provider
    previous_orderbook = settings.steam_orderbook_enabled
    settings.market_provider = "steam"
    settings.steam_orderbook_enabled = True
    db_session.add_all(
        [
            Item(market_hash_name="ready", display_name="Ready", steam_item_nameid="123", is_active=True),
            Item(market_hash_name="missing", display_name="Missing", steam_item_nameid="", is_active=True),
        ]
    )
    db_session.commit()
    app.dependency_overrides[get_db] = override_session(db_session)
    client = TestClient(app)
    try:
        response = client.get("/api/source/config")
    finally:
        settings.market_provider = previous_provider
        settings.steam_orderbook_enabled = previous_orderbook
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "steam"
    assert body["steam_orderbook_enabled"] is True
    assert body["active_item_count"] == 2
    assert body["active_nameid_count"] == 1
    assert body["active_nameid_coverage_rate"] == 0.5
    assert body["readiness"] == "partial"


def test_p0_summary_reports_blockers_for_empty_state(db_session):
    previous_provider = settings.market_provider
    settings.market_provider = "mock"
    app.dependency_overrides[get_db] = override_session(db_session)
    client = TestClient(app)
    try:
        response = client.get("/api/ops/p0-summary")
    finally:
        settings.market_provider = previous_provider
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["ready"] is False
    assert body["status"] == "blocked"
    assert body["blockers"]
    assert body["source_config"]["readiness"] == "mock"


def test_p0_summary_reports_ready_when_requirements_are_met(db_session):
    previous_provider = settings.market_provider
    previous_orderbook = settings.steam_orderbook_enabled
    settings.market_provider = "steam"
    settings.steam_orderbook_enabled = True
    platform = Platform(code="steam", name="Steam")
    items = [
        Item(market_hash_name=f"ready-{index}", display_name=f"Ready {index}", steam_item_nameid=str(index), is_active=True)
        for index in range(5)
    ]
    db_session.add(platform)
    db_session.add_all(items)
    db_session.flush()
    start = datetime.utcnow() - timedelta(days=8)
    for index in range(9):
        db_session.add(
            CollectRunLog(
                mode="worker",
                provider="steam",
                status="success",
                item_count=5,
                snapshot_count=5,
                started_at=start + timedelta(days=index),
                finished_at=start + timedelta(days=index, minutes=1),
            )
        )
    quality = json.dumps(
        {
            "source_quality": {
                "real_fields": ["lowest_price", "sell_count", "highest_buy_price", "buy_count", "volume_24h", "avg_price_24h"],
                "fallback_fields": [],
            }
        }
    )
    for item in items:
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
                raw_payload=quality,
            )
        )
    db_session.commit()
    app.dependency_overrides[get_db] = override_session(db_session)
    client = TestClient(app)
    try:
        response = client.get("/api/ops/p0-summary")
    finally:
        settings.market_provider = previous_provider
        settings.steam_orderbook_enabled = previous_orderbook
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["ready"] is True
    assert body["status"] == "ready"
    assert body["blockers"] == []
    assert body["readiness"]["ready_for_7d_review"] is True
    assert body["source_config"]["readiness"] == "ready"


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


def create_backup_scripts(root: Path) -> None:
    scripts = root / "scripts"
    scripts.mkdir(parents=True)
    (scripts / "backup_postgres.sh").write_text("postgres backup", encoding="utf-8")
    (scripts / "backup_config.sh").write_text("config backup", encoding="utf-8")


def create_backup_cron(root: Path) -> None:
    cron = root / "backups" / "cron"
    cron.mkdir(parents=True)
    (cron / "cs-quant-backup").write_text(
        "10 3 * * * app cd /app && bash scripts/backup_postgres.sh\n"
        "40 3 * * * app cd /app && bash scripts/backup_config.sh\n",
        encoding="utf-8",
    )
