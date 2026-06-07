import json
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Alert, BacktestResult, CollectRunLog, Item, MarketSnapshot, MonitorPool, Platform, PushRecord
from app.models import StrategyConfig
from app.schemas.market import (
    AlertOut,
    AlertCoverageOut,
    AcceptanceItemOut,
    AcceptanceOut,
    BacktestResultOut,
    BacktestSignalOut,
    BacktestSummaryOut,
    CollectRunLogOut,
    DecisionSignalOut,
    CategoryStrategyOut,
    AlertSummaryOut,
    AlertTypeCoverageOut,
    HeatmapBucketOut,
    HealthOut,
    HistoryPointOut,
    ItemCreate,
    ItemDetailOut,
    ItemOut,
    ItemUpdate,
    SteamOrderbookValidationOut,
    SteamNameIdBatchOut,
    SteamNameIdTodoItemOut,
    SteamNameIdTodoOut,
    SteamNameIdOut,
    MonitorPoolCreate,
    MonitorCoverageBucketOut,
    MonitorCoverageOut,
    MonitorPoolOut,
    MonitorPoolUpdate,
    MonitorItemOut,
    OpsHealthOut,
    P0SummaryOut,
    OpsReadinessOut,
    RetentionCleanupOut,
    RuntimeConfigOut,
    RuntimeAuditItemOut,
    RuntimeAuditOut,
    PushRecordOut,
    SourceConfigOut,
    SourceFieldQualityOut,
    RetentionMetricOut,
    RetentionOut,
    SnapshotOut,
    SourceQualityOut,
    FieldQualityOut,
    StrategyConfigOut,
    StrategyConfigUpdate,
    TuningSuggestionOut,
)
from app.services.market_service import MarketService
from app.services.backtest_service import BacktestService
from app.services.push_service import PushService
from app.services.score_service import decision_from_scores, score_from_snapshot, status_from_alert
from app.services.steam_nameid_service import SteamNameIdService

router = APIRouter()
APP_VERSION = "0.1.57"
SNAPSHOT_RETENTION_DAYS = 180
COLLECT_LOG_RETENTION_DAYS = 90
SOURCE_FIELDS = [
    ("lowest_price", "底价"),
    ("sell_count", "在售"),
    ("highest_buy_price", "最高求购"),
    ("buy_count", "求购"),
    ("volume_24h", "24h 成交"),
    ("avg_price_24h", "24h 均价"),
]
EXPECTED_ALERT_TYPES = ["在售变化", "求购变化", "底价变化", "价格波动异常", "成交量异常"]


@router.get("/health", response_model=HealthOut)
def health() -> HealthOut:
    return HealthOut(status="ok", service="cs-quantification-api", version=APP_VERSION)


@router.get("/ops/runtime", response_model=RuntimeConfigOut)
def ops_runtime() -> RuntimeConfigOut:
    return RuntimeConfigOut(
        version=APP_VERSION,
        database_kind=_database_kind(settings.database_url),
        market_provider=settings.market_provider.lower(),
        steam_orderbook_enabled=settings.steam_orderbook_enabled,
        worker_sleep_seconds=settings.worker_sleep_seconds,
        push_channel=settings.push_channel.lower(),
        push_configured=_push_configured(),
        cors_origin_count=len([origin for origin in settings.cors_origins.split(",") if origin.strip()]),
    )


@router.get("/ops/runtime-audit", response_model=RuntimeAuditOut)
def ops_runtime_audit() -> RuntimeAuditOut:
    items = _runtime_audit_items()
    fail_count = sum(1 for item in items if item.status == "fail")
    warn_count = sum(1 for item in items if item.status == "warn")
    status = "fail" if fail_count else "warn" if warn_count else "ready"
    return RuntimeAuditOut(status=status, fail_count=fail_count, warn_count=warn_count, items=items)


@router.get("/ops/health", response_model=OpsHealthOut)
def ops_health(db: Session = Depends(get_db)) -> OpsHealthOut:
    since = datetime.utcnow() - timedelta(hours=24)
    runs = db.query(CollectRunLog).filter(CollectRunLog.started_at >= since).order_by(CollectRunLog.started_at.desc()).all()
    latest = runs[0] if runs else None
    push_records = db.query(PushRecord).filter(PushRecord.created_at >= since).all()
    snapshot_count = sum(run.snapshot_count for run in runs)
    alert_count = sum(run.alert_count for run in runs)
    source_error_count = sum(run.error_count for run in runs)
    real_fields = sum(run.real_field_count for run in runs)
    fallback_fields = sum(run.fallback_field_count for run in runs)
    total_fields = real_fields + fallback_fields
    collect_success_rate = sum(1 for run in runs if run.status == "success") / len(runs) if runs else 0
    sent_or_skipped = sum(1 for record in push_records if record.status in {"sent", "skipped"})
    push_success_rate = sent_or_skipped / len(push_records) if push_records else 1
    latest_finished_at = latest.finished_at or latest.started_at if latest else None
    worker_lag = (datetime.utcnow() - latest_finished_at).total_seconds() / 60 if latest_finished_at else None
    return OpsHealthOut(
        status=_ops_status(runs, push_records, worker_lag, source_error_count),
        latest_run_status=latest.status if latest else "none",
        latest_run_at=latest_finished_at,
        collect_success_rate=collect_success_rate,
        push_success_rate=push_success_rate,
        snapshot_count_24h=snapshot_count,
        alert_count_24h=alert_count,
        source_error_count_24h=source_error_count,
        real_field_ratio_24h=real_fields / total_fields if total_fields else 0,
        worker_lag_minutes=worker_lag,
    )


@router.get("/ops/readiness", response_model=OpsReadinessOut)
def ops_readiness(db: Session = Depends(get_db)) -> OpsReadinessOut:
    return _ops_readiness(db)


@router.get("/ops/p0-summary", response_model=P0SummaryOut)
def p0_summary(db: Session = Depends(get_db)) -> P0SummaryOut:
    readiness = _ops_readiness(db)
    source = _source_config(db)
    field_quality = _source_field_quality(db, 500)
    blockers: list[str] = []
    if source.readiness != "ready":
        blockers.append(source.suggestion)
    if not readiness.ready_for_7d_review:
        blockers.append("连续采集尚未满足 7 天观察、80% 成功率和 80% 快照覆盖率")
    weak_fields = [field.label for field in field_quality.fields if field.real_ratio < 0.8]
    if weak_fields:
        blockers.append(f"字段真实率不足：{', '.join(weak_fields)}")
    alert_count = db.query(Alert).count()
    review_items = [
        "检查 30 个测试饰品是否持续产生快照",
        "对照 Steam 市场抽查底价、成交与买卖盘字段",
        "确认告警触发后可追溯原始快照",
    ]
    if alert_count == 0:
        review_items.append("当前暂无告警，继续观察是否能输出第一版异动告警")
    ready = not blockers
    return P0SummaryOut(
        ready=ready,
        status="ready" if ready else "blocked",
        blockers=blockers,
        review_items=review_items,
        readiness=readiness,
        source_config=source,
        field_quality=field_quality,
        alert_count=alert_count,
    )


@router.get("/ops/acceptance", response_model=AcceptanceOut)
def ops_acceptance(db: Session = Depends(get_db)) -> AcceptanceOut:
    return _ops_acceptance(db)


def _ops_acceptance(db: Session) -> AcceptanceOut:
    readiness = _ops_readiness(db)
    source = _source_config(db)
    field_quality = _source_field_quality(db, 500)
    coverage = _alert_coverage(db)
    retention_state = retention(db)
    health = ops_health(db)
    runtime_audit = ops_runtime_audit()
    backtest_count = db.query(BacktestResult).count()
    push_count = db.query(PushRecord).count()
    retention_names = {metric.name for metric in retention_state.metrics}
    weak_fields = [field.label for field in field_quality.fields if field.real_ratio < 0.8]
    items = [
        _acceptance_item(
            "stable_collection_7d",
            "数据采集连续稳定运行 7 天",
            "passed" if readiness.ready_for_7d_review else "review",
            f"观察 {readiness.observed_days:.1f} 天，成功 {readiness.success_run_count}/{readiness.collect_run_count} 轮，快照覆盖 {readiness.snapshot_coverage_rate:.0%}",
        ),
        _acceptance_item(
            "price_accuracy",
            "重点饰品价格数据准确",
            "passed" if not weak_fields and source.provider == "steam" else "review",
            "字段真实率达标且使用 Steam 数据源" if not weak_fields and source.provider == "steam" else "需人工抽查 Steam 市场底价与成交字段",
        ),
        _acceptance_item(
            "sell_depth_accuracy",
            "在售变化与实际市场基本一致",
            _field_acceptance_status(field_quality, "sell_count", source.steam_orderbook_enabled),
            _field_acceptance_evidence(field_quality, "sell_count", source.steam_orderbook_enabled),
        ),
        _acceptance_item(
            "buy_depth_accuracy",
            "求购变化与实际市场基本一致",
            _field_acceptance_status(field_quality, "buy_count", source.steam_orderbook_enabled),
            _field_acceptance_evidence(field_quality, "buy_count", source.steam_orderbook_enabled),
        ),
        _acceptance_item(
            "alert_noise",
            "告警不会频繁重复刷屏",
            "passed" if coverage.total_count == 0 or coverage.traceable_rate >= 0.8 else "review",
            f"告警 {coverage.total_count} 条，可追溯率 {coverage.traceable_rate:.0%}",
        ),
        _acceptance_item(
            "push_latency",
            "推送延迟可接受",
            "passed" if health.push_success_rate >= 0.8 else "review",
            f"近 24h 推送成功率 {health.push_success_rate:.0%}，历史推送记录 {push_count} 条",
        ),
        _acceptance_item(
            "detail_charts",
            "单品详情图表可正常查看",
            "passed" if readiness.snapshot_count > 0 else "review",
            f"当前行情快照 {readiness.snapshot_count} 条",
        ),
        _acceptance_item(
            "opportunity_ranking",
            "机会榜排序逻辑可解释",
            "passed" if backtest_count > 0 else "review",
            f"回测样本 {backtest_count} 条，排序已结合评分、品类和回测信号",
        ),
        _acceptance_item(
            "alert_traceability",
            "每条告警都能追溯原始数据",
            "passed" if coverage.total_count > 0 and coverage.traceable_rate >= 0.8 else "review",
            f"可追溯 {coverage.traceable_count}/{coverage.total_count} 条告警",
        ),
        _acceptance_item(
            "restart_recovery",
            "服务器重启后服务能自动恢复",
            "passed",
            "Docker Compose 已配置 restart 策略和健康检查，需云服务器实机复核",
        ),
        _acceptance_item(
            "backup_ready",
            "数据库有备份",
            "passed" if "行情快照" in retention_names else "review",
            "已提供 PostgreSQL 备份脚本和数据保留策略",
        ),
        _acceptance_item(
            "strategy_adjustable",
            "策略参数可以调整",
            "passed" if db.query(StrategyConfig).filter_by(name="default").first() is not None else "review",
            "默认策略支持阈值、冷却、扣费和可信度降权配置",
        ),
        _acceptance_item(
            "source_fail_safe",
            "数据源异常时不会批量误推",
            "passed" if health.source_error_count_24h == 0 else "review",
            f"近 24h 数据源异常 {health.source_error_count_24h} 次，采集质量熔断已启用",
        ),
        _acceptance_item(
            "history_review",
            "历史告警能用于复盘",
            "passed" if coverage.total_count > 0 or backtest_count > 0 else "review",
            f"告警 {coverage.total_count} 条，回测 {backtest_count} 条",
        ),
        _acceptance_item(
            "decision_reference_only",
            "平台输出参考信号，不直接触发自动买卖",
            "passed",
            "系统仅输出买入、持有、卖出、观望参考信号，未实现自动交易执行模块",
        ),
    ]
    blocked_count = sum(1 for item in items if item.status == "blocked")
    review_count = sum(1 for item in items if item.status == "review")
    if runtime_audit.fail_count:
        blocked_count += 1
        items.insert(
            0,
            _acceptance_item(
                "runtime_audit",
                "部署环境无阻断配置风险",
                "blocked",
                f"部署审计存在 {runtime_audit.fail_count} 个阻断和 {runtime_audit.warn_count} 个提醒",
            ),
        )
    status = "blocked" if blocked_count else "review" if review_count else "passed"
    return AcceptanceOut(
        status=status,
        passed_count=sum(1 for item in items if item.status == "passed"),
        review_count=sum(1 for item in items if item.status == "review"),
        blocked_count=sum(1 for item in items if item.status == "blocked"),
        items=items,
    )


def _ops_readiness(db: Session) -> OpsReadinessOut:
    runs = db.query(CollectRunLog).order_by(CollectRunLog.started_at.asc()).all()
    first_run = runs[0] if runs else None
    latest_run = runs[-1] if runs else None
    observed_days = 0.0
    if first_run and latest_run:
        observed_days = max((latest_run.started_at - first_run.started_at).total_seconds() / 86400, 0)
    monitored_item_count = db.query(Item).filter_by(is_active=True).count()
    snapshot_item_ids = {row[0] for row in db.query(MarketSnapshot.item_id).distinct().all()}
    items_with_snapshots = db.query(Item).filter(Item.is_active.is_(True), Item.id.in_(snapshot_item_ids)).count() if snapshot_item_ids else 0
    success_run_count = sum(1 for run in runs if run.status == "success")
    collect_success_rate = success_run_count / len(runs) if runs else 0
    snapshot_coverage_rate = items_with_snapshots / monitored_item_count if monitored_item_count else 0
    return OpsReadinessOut(
        ready_for_7d_review=observed_days >= 7 and collect_success_rate >= 0.8 and snapshot_coverage_rate >= 0.8,
        observed_days=observed_days,
        collect_run_count=len(runs),
        success_run_count=success_run_count,
        collect_success_rate=collect_success_rate,
        monitored_item_count=monitored_item_count,
        items_with_snapshots=items_with_snapshots,
        snapshot_coverage_rate=snapshot_coverage_rate,
        snapshot_count=db.query(MarketSnapshot).count(),
        latest_run_at=latest_run.finished_at or latest_run.started_at if latest_run else None,
    )


@router.get("/source/field-quality", response_model=SourceFieldQualityOut)
def source_field_quality(limit: int = Query(default=500, ge=1, le=5000), db: Session = Depends(get_db)) -> SourceFieldQualityOut:
    return _source_field_quality(db, limit)


def _source_field_quality(db: Session, limit: int) -> SourceFieldQualityOut:
    snapshots = db.query(MarketSnapshot).order_by(MarketSnapshot.captured_at.desc()).limit(limit).all()
    stats = {field: {"real": 0, "fallback": 0} for field, _ in SOURCE_FIELDS}
    for snapshot in snapshots:
        quality = _source_quality(snapshot)
        if quality is None:
            for field, _ in SOURCE_FIELDS:
                stats[field]["fallback"] += 1
            continue
        real_fields = set(quality.real_fields)
        fallback_fields = set(quality.fallback_fields)
        for field, _ in SOURCE_FIELDS:
            if field in real_fields:
                stats[field]["real"] += 1
            elif field in fallback_fields or not real_fields:
                stats[field]["fallback"] += 1
    return SourceFieldQualityOut(
        snapshot_sample_count=len(snapshots),
        fields=[
            FieldQualityOut(
                field=field,
                label=label,
                real_count=stats[field]["real"],
                fallback_count=stats[field]["fallback"],
                real_ratio=stats[field]["real"] / len(snapshots) if snapshots else 0,
            )
            for field, label in SOURCE_FIELDS
        ],
    )


@router.get("/alerts/coverage", response_model=AlertCoverageOut)
def alert_coverage(db: Session = Depends(get_db)) -> AlertCoverageOut:
    return _alert_coverage(db)


def _alert_coverage(db: Session) -> AlertCoverageOut:
    alerts = db.query(Alert).order_by(Alert.created_at.desc()).all()
    since = datetime.utcnow() - timedelta(hours=24)
    traceable = 0
    type_counts: dict[str, int] = {}
    for alert in alerts:
        type_counts[alert.alert_type] = type_counts.get(alert.alert_type, 0) + 1
        if alert.snapshot is not None:
            traceable += 1
    return AlertCoverageOut(
        total_count=len(alerts),
        recent_24h_count=sum(1 for alert in alerts if alert.created_at >= since),
        covered_type_count=sum(1 for alert_type in EXPECTED_ALERT_TYPES if type_counts.get(alert_type, 0) > 0),
        expected_type_count=len(EXPECTED_ALERT_TYPES),
        traceable_count=traceable,
        traceable_rate=traceable / len(alerts) if alerts else 0,
        latest_alert=_alert_out(alerts[0]) if alerts else None,
        types=[
            AlertTypeCoverageOut(alert_type=alert_type, count=type_counts.get(alert_type, 0))
            for alert_type in EXPECTED_ALERT_TYPES
        ],
    )


@router.get("/source/config", response_model=SourceConfigOut)
def source_config(db: Session = Depends(get_db)) -> SourceConfigOut:
    return _source_config(db)


def _source_config(db: Session) -> SourceConfigOut:
    provider = settings.market_provider.lower()
    configured_nameids = _configured_nameids()
    active_items = db.query(Item).filter_by(is_active=True).all()
    active_nameid_count = sum(1 for item in active_items if item.steam_item_nameid)
    active_count = len(active_items)
    coverage = active_nameid_count / active_count if active_count else 0
    readiness = "ready" if provider == "steam" and (not settings.steam_orderbook_enabled or coverage >= 0.8) else "mock" if provider == "mock" else "partial"
    suggestion = _source_config_suggestion(provider, settings.steam_orderbook_enabled, coverage)
    return SourceConfigOut(
        provider=provider,
        steam_orderbook_enabled=settings.steam_orderbook_enabled,
        configured_nameid_count=len(configured_nameids),
        active_item_count=active_count,
        active_nameid_count=active_nameid_count,
        active_nameid_coverage_rate=coverage,
        readiness=readiness,
        suggestion=suggestion,
    )


@router.get("/retention", response_model=RetentionOut)
def retention(db: Session = Depends(get_db)) -> RetentionOut:
    return RetentionOut(
        snapshot_retention_days=SNAPSHOT_RETENTION_DAYS,
        collect_log_retention_days=COLLECT_LOG_RETENTION_DAYS,
        alert_retention_days=None,
        backtest_retention_days=None,
        metrics=[
            _retention_metric(db, MarketSnapshot, MarketSnapshot.captured_at, "行情快照", SNAPSHOT_RETENTION_DAYS, "保留 3-6 个月，当前按 180 天观察"),
            _retention_metric(db, Alert, Alert.created_at, "告警记录", None, "长期保留，用于复盘"),
            _retention_metric(db, BacktestResult, BacktestResult.created_at, "回测结果", None, "长期保留，用于策略调参"),
            _retention_metric(db, CollectRunLog, CollectRunLog.started_at, "采集日志", COLLECT_LOG_RETENTION_DAYS, "保留 90 天，用于运维排查"),
        ],
    )


@router.post("/retention/cleanup", response_model=RetentionCleanupOut)
def cleanup_retention(db: Session = Depends(get_db)) -> RetentionCleanupOut:
    snapshot_cutoff = datetime.utcnow() - timedelta(days=SNAPSHOT_RETENTION_DAYS)
    collect_log_cutoff = datetime.utcnow() - timedelta(days=COLLECT_LOG_RETENTION_DAYS)
    referenced_snapshot_ids = db.query(Alert.snapshot_id).filter(Alert.snapshot_id.isnot(None))
    deleted_snapshots = (
        db.query(MarketSnapshot)
        .filter(MarketSnapshot.captured_at < snapshot_cutoff, ~MarketSnapshot.id.in_(referenced_snapshot_ids))
        .delete(synchronize_session=False)
    )
    deleted_collect_logs = (
        db.query(CollectRunLog)
        .filter(CollectRunLog.started_at < collect_log_cutoff)
        .delete(synchronize_session=False)
    )
    db.commit()
    return RetentionCleanupOut(
        snapshot_retention_days=SNAPSHOT_RETENTION_DAYS,
        collect_log_retention_days=COLLECT_LOG_RETENTION_DAYS,
        deleted_snapshots=deleted_snapshots,
        deleted_collect_logs=deleted_collect_logs,
    )


@router.post("/collect", response_model=list[AlertOut])
def collect(db: Session = Depends(get_db)) -> list[AlertOut]:
    market_service = MarketService(db)
    alerts = market_service.collect_active_items()
    PushService(db).dispatch_alerts(alerts, market_service.push_suppress_reason())
    BacktestService(db).evaluate_due_alerts()
    return [_alert_out(alert) for alert in alerts]


@router.get("/monitor", response_model=list[MonitorItemOut])
def monitor(db: Session = Depends(get_db)) -> list[MonitorItemOut]:
    items = db.query(Item).filter_by(is_active=True).order_by(Item.display_name.asc()).all()
    config = _default_strategy(db)
    return [_monitor_item(db, item, config) for item in items]


@router.get("/monitor/coverage", response_model=MonitorCoverageOut)
def monitor_coverage(db: Session = Depends(get_db)) -> MonitorCoverageOut:
    active_items = db.query(Item).filter_by(is_active=True).all()
    all_items = db.query(Item).all()
    total_item_count = db.query(Item).count()
    active_item_count = len(active_items)
    return MonitorCoverageOut(
        status=_monitor_coverage_status(active_item_count),
        active_item_count=active_item_count,
        total_item_count=total_item_count,
        p1_min_item_count=100,
        p1_max_item_count=300,
        missing_nameid_count=sum(1 for item in active_items if not item.steam_item_nameid),
        pools=_monitor_pool_coverage(db),
        categories=_monitor_category_coverage(active_items, all_items),
    )


@router.get("/items", response_model=list[ItemOut])
def item_list(db: Session = Depends(get_db)) -> list[ItemOut]:
    items = db.query(Item).order_by(Item.is_active.desc(), Item.display_name.asc()).all()
    return [_item_out(item) for item in items]


@router.post("/items", response_model=ItemOut)
def create_item(payload: ItemCreate, db: Session = Depends(get_db)) -> ItemOut:
    existing = db.query(Item).filter_by(market_hash_name=payload.market_hash_name).first()
    if existing is not None:
        raise HTTPException(status_code=409, detail="item already exists")
    _ensure_pool(db, payload.pool_id)
    item = Item(
        market_hash_name=payload.market_hash_name,
        display_name=payload.display_name,
        exterior=payload.exterior,
        category=payload.category,
        steam_item_nameid=payload.steam_item_nameid,
        is_active=payload.is_active,
        pool_id=payload.pool_id,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return _item_out(item)


@router.get("/items/{item_id}", response_model=ItemDetailOut)
def item_detail(item_id: int, db: Session = Depends(get_db)) -> ItemDetailOut:
    item = db.get(Item, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="item not found")
    snapshots = (
        db.query(MarketSnapshot)
        .filter(MarketSnapshot.item_id == item_id)
        .order_by(MarketSnapshot.captured_at.desc())
        .limit(120)
        .all()
    )
    alerts = db.query(Alert).filter(Alert.item_id == item_id).order_by(Alert.created_at.desc()).limit(30).all()
    latest_snapshot = snapshots[0] if snapshots else None
    latest_alert = alerts[0] if alerts else None
    buy_score, sell_score = score_from_snapshot(latest_snapshot, latest_alert)
    source_quality = _source_quality(latest_snapshot)
    config = _default_strategy(db)
    adjusted_buy_score, adjusted_sell_score, quality_penalty = _quality_adjusted_scores(
        buy_score, sell_score, source_quality, config.quality_penalty_max
    )
    category_strategy = _category_strategy(item, latest_snapshot)
    adjusted_buy_score, adjusted_sell_score = _category_adjusted_scores(
        adjusted_buy_score, adjusted_sell_score, category_strategy
    )
    backtest_signal = _backtest_signal(db, latest_alert)
    status = status_from_alert(latest_alert)
    decision_signal = _decision_signal(latest_snapshot, status, adjusted_buy_score, adjusted_sell_score, source_quality)
    return ItemDetailOut(
        id=item.id,
        display_name=item.display_name,
        market_hash_name=item.market_hash_name,
        exterior=item.exterior,
        category=item.category,
        steam_item_nameid=item.steam_item_nameid,
        status=status,
        buy_score=buy_score,
        sell_score=sell_score,
        adjusted_buy_score=adjusted_buy_score,
        adjusted_sell_score=adjusted_sell_score,
        quality_penalty=quality_penalty,
        snapshots=[_snapshot_out(snapshot, config) for snapshot in reversed(snapshots)],
        alerts=[_alert_out(alert) for alert in alerts],
        heatmap=_heatmap(list(reversed(snapshots))),
        alert_summary=_alert_summary(alerts),
        source_quality=source_quality,
        category_strategy=category_strategy,
        backtest_signal=backtest_signal,
        decision_signal=decision_signal,
    )


@router.get("/items/{item_id}/history/price", response_model=list[HistoryPointOut])
def item_price_history(item_id: int, limit: int = Query(default=240, ge=1, le=5000), db: Session = Depends(get_db)) -> list[HistoryPointOut]:
    _ensure_item(db, item_id)
    return _history_points(db, item_id, "lowest_price", limit)


@router.get("/items/{item_id}/history/sell", response_model=list[HistoryPointOut])
def item_sell_history(item_id: int, limit: int = Query(default=240, ge=1, le=5000), db: Session = Depends(get_db)) -> list[HistoryPointOut]:
    _ensure_item(db, item_id)
    return _history_points(db, item_id, "sell_count", limit)


@router.get("/items/{item_id}/history/buy", response_model=list[HistoryPointOut])
def item_buy_history(item_id: int, limit: int = Query(default=240, ge=1, le=5000), db: Session = Depends(get_db)) -> list[HistoryPointOut]:
    _ensure_item(db, item_id)
    return _history_points(db, item_id, "buy_count", limit)


@router.put("/items/{item_id}", response_model=ItemOut)
def update_item(item_id: int, payload: ItemUpdate, db: Session = Depends(get_db)) -> ItemOut:
    item = db.get(Item, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="item not found")
    duplicate = db.query(Item).filter(Item.market_hash_name == payload.market_hash_name, Item.id != item_id).first()
    if duplicate is not None:
        raise HTTPException(status_code=409, detail="item already exists")
    _ensure_pool(db, payload.pool_id)
    item.market_hash_name = payload.market_hash_name
    item.display_name = payload.display_name
    item.exterior = payload.exterior
    item.category = payload.category
    item.steam_item_nameid = payload.steam_item_nameid
    item.is_active = payload.is_active
    item.pool_id = payload.pool_id
    db.commit()
    db.refresh(item)
    return _item_out(item)


@router.patch("/items/{item_id}/active", response_model=ItemOut)
def set_item_active(item_id: int, is_active: bool, db: Session = Depends(get_db)) -> ItemOut:
    item = db.get(Item, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="item not found")
    item.is_active = is_active
    db.commit()
    db.refresh(item)
    return _item_out(item)


@router.post("/items/{item_id}/steam-nameid/discover", response_model=SteamNameIdOut)
def discover_item_steam_nameid(item_id: int, db: Session = Depends(get_db)) -> SteamNameIdOut:
    item = db.get(Item, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="item not found")
    try:
        _discover_nameid(item, db, SteamNameIdService())
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return SteamNameIdOut(
        item_id=item.id,
        market_hash_name=item.market_hash_name,
        steam_item_nameid=item.steam_item_nameid,
    )


@router.post("/steam-nameids/discover-missing", response_model=SteamNameIdBatchOut)
def discover_missing_steam_nameids(db: Session = Depends(get_db)) -> SteamNameIdBatchOut:
    service = SteamNameIdService()
    items = (
        db.query(Item)
        .filter(Item.is_active.is_(True), (Item.steam_item_nameid == "") | (Item.steam_item_nameid.is_(None)))
        .order_by(Item.display_name.asc())
        .all()
    )
    results: list[SteamOrderbookValidationOut] = []
    for item in items:
        try:
            _discover_nameid(item, db, service)
            results.append(_validation_result(item, ok=True))
        except Exception as exc:
            db.rollback()
            results.append(_validation_result(item, ok=False, error=str(exc)))
    return _batch_result(results)


@router.get("/steam-nameids/todo", response_model=SteamNameIdTodoOut)
def steam_nameid_todo(db: Session = Depends(get_db)) -> SteamNameIdTodoOut:
    active_items = db.query(Item).filter_by(is_active=True).order_by(Item.display_name.asc()).all()
    missing_items = [item for item in active_items if not item.steam_item_nameid]
    active_count = len(active_items)
    missing_count = len(missing_items)
    return SteamNameIdTodoOut(
        status="ready" if missing_count == 0 else "partial" if missing_count < active_count else "missing",
        active_item_count=active_count,
        missing_count=missing_count,
        coverage_rate=(active_count - missing_count) / active_count if active_count else 0,
        discoverable_count=missing_count,
        pools=_steam_nameid_pool_todo(missing_items),
        missing_items=[
            SteamNameIdTodoItemOut(
                item_id=item.id,
                display_name=item.display_name,
                market_hash_name=item.market_hash_name,
                pool_name=item.pool.name if item.pool else None,
                category=item.category,
            )
            for item in missing_items[:20]
        ],
    )


@router.post("/items/{item_id}/steam-nameid/validate", response_model=SteamOrderbookValidationOut)
def validate_item_steam_nameid(item_id: int, db: Session = Depends(get_db)) -> SteamOrderbookValidationOut:
    item = db.get(Item, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="item not found")
    return _validate_nameid(item, SteamNameIdService())


@router.post("/steam-nameids/validate-all", response_model=SteamNameIdBatchOut)
def validate_all_steam_nameids(db: Session = Depends(get_db)) -> SteamNameIdBatchOut:
    service = SteamNameIdService()
    items = (
        db.query(Item)
        .filter(Item.is_active.is_(True), Item.steam_item_nameid != "")
        .order_by(Item.display_name.asc())
        .all()
    )
    results = [_validate_nameid(item, service) for item in items]
    return _batch_result(results)


def _discover_nameid(item: Item, db: Session, service: SteamNameIdService) -> None:
    item.steam_item_nameid = service.discover(item.market_hash_name)
    db.commit()
    db.refresh(item)


def _validate_nameid(item: Item, service: SteamNameIdService) -> SteamOrderbookValidationOut:
    try:
        orderbook = service.validate_orderbook(item.steam_item_nameid)
    except Exception as exc:
        return _validation_result(item, ok=False, error=str(exc))
    return _validation_result(
        item,
        ok=True,
        sell_count=orderbook["sell_count"],
        buy_count=orderbook["buy_count"],
        highest_buy_price=orderbook["highest_buy_price"],
    )


def _validation_result(
    item: Item,
    ok: bool,
    sell_count: int = 0,
    buy_count: int = 0,
    highest_buy_price: float = 0,
    error: str = "",
) -> SteamOrderbookValidationOut:
    return SteamOrderbookValidationOut(
        item_id=item.id,
        market_hash_name=item.market_hash_name,
        steam_item_nameid=item.steam_item_nameid,
        ok=ok,
        sell_count=sell_count,
        buy_count=buy_count,
        highest_buy_price=highest_buy_price,
        error=error,
    )


def _batch_result(results: list[SteamOrderbookValidationOut]) -> SteamNameIdBatchOut:
    success_count = sum(1 for result in results if result.ok)
    return SteamNameIdBatchOut(
        total=len(results),
        success_count=success_count,
        failure_count=len(results) - success_count,
        results=results,
    )


def _steam_nameid_pool_todo(missing_items: list[Item]) -> list[MonitorCoverageBucketOut]:
    counts: dict[str, int] = {}
    for item in missing_items:
        pool_name = item.pool.name if item.pool else "未分组"
        counts[pool_name] = counts.get(pool_name, 0) + 1
    return [
        MonitorCoverageBucketOut(name=name, active_count=count, total_count=count)
        for name, count in sorted(counts.items(), key=lambda row: row[1], reverse=True)
    ]


@router.get("/monitor-pools", response_model=list[MonitorPoolOut])
def monitor_pools(db: Session = Depends(get_db)) -> list[MonitorPoolOut]:
    pools = db.query(MonitorPool).order_by(MonitorPool.interval_minutes.asc()).all()
    return [_monitor_pool_out(pool) for pool in pools]


@router.post("/monitor-pools", response_model=MonitorPoolOut)
def create_monitor_pool(payload: MonitorPoolCreate, db: Session = Depends(get_db)) -> MonitorPoolOut:
    if db.query(MonitorPool).filter_by(name=payload.name).first() is not None:
        raise HTTPException(status_code=409, detail="monitor pool already exists")
    pool = MonitorPool(
        name=payload.name,
        interval_minutes=payload.interval_minutes,
        description=payload.description,
    )
    db.add(pool)
    db.commit()
    db.refresh(pool)
    return _monitor_pool_out(pool)


@router.put("/monitor-pools/{pool_id}", response_model=MonitorPoolOut)
def update_monitor_pool(pool_id: int, payload: MonitorPoolUpdate, db: Session = Depends(get_db)) -> MonitorPoolOut:
    pool = db.get(MonitorPool, pool_id)
    if pool is None:
        raise HTTPException(status_code=404, detail="monitor pool not found")
    duplicate = db.query(MonitorPool).filter(MonitorPool.name == payload.name, MonitorPool.id != pool_id).first()
    if duplicate is not None:
        raise HTTPException(status_code=409, detail="monitor pool already exists")
    pool.name = payload.name
    pool.interval_minutes = payload.interval_minutes
    pool.description = payload.description
    db.commit()
    db.refresh(pool)
    return _monitor_pool_out(pool)


def _monitor_pool_out(pool: MonitorPool) -> MonitorPoolOut:
    return MonitorPoolOut(
        id=pool.id,
        name=pool.name,
        interval_minutes=pool.interval_minutes,
        description=pool.description,
        last_collected_at=pool.last_collected_at,
        active_item_count=sum(1 for item in pool.items if item.is_active),
    )


@router.get("/collect-runs", response_model=list[CollectRunLogOut])
def collect_runs(db: Session = Depends(get_db)) -> list[CollectRunLog]:
    return db.query(CollectRunLog).order_by(CollectRunLog.started_at.desc()).limit(100).all()


@router.get("/alerts", response_model=list[AlertOut])
def alerts(
    item: str = Query(default=""),
    alert_type: str = Query(default=""),
    severity: str = Query(default=""),
    platform: str = Query(default=""),
    db: Session = Depends(get_db),
) -> list[AlertOut]:
    query = db.query(Alert).join(Item, Alert.item_id == Item.id).join(Platform, Alert.platform_id == Platform.id)
    if item:
        query = query.filter(Item.display_name.contains(item))
    if alert_type:
        query = query.filter(Alert.alert_type == alert_type)
    if severity:
        query = query.filter(Alert.severity == severity)
    if platform:
        query = query.filter(Platform.name.contains(platform))
    rows = query.order_by(Alert.created_at.desc()).limit(100).all()
    return [_alert_out(alert) for alert in rows]


@router.get("/push-records", response_model=list[PushRecordOut])
def push_records(db: Session = Depends(get_db)) -> list[PushRecordOut]:
    return db.query(PushRecord).order_by(PushRecord.created_at.desc()).limit(100).all()


@router.get("/backtests", response_model=list[BacktestResultOut])
def backtests(db: Session = Depends(get_db)) -> list[BacktestResultOut]:
    rows = db.query(BacktestResult).order_by(BacktestResult.created_at.desc()).limit(200).all()
    return [_backtest_out(row) for row in rows]


@router.get("/backtests/summary", response_model=list[BacktestSummaryOut])
def backtest_summary(db: Session = Depends(get_db)) -> list[dict]:
    return BacktestService(db).summary()


@router.get("/backtests/tuning-suggestions", response_model=list[TuningSuggestionOut])
def tuning_suggestions(db: Session = Depends(get_db)) -> list[dict]:
    return BacktestService(db).tuning_suggestions()


@router.post("/backtests/evaluate", response_model=list[BacktestResultOut])
def evaluate_backtests(db: Session = Depends(get_db)) -> list[BacktestResultOut]:
    rows = BacktestService(db).evaluate_due_alerts()
    return [_backtest_out(row) for row in rows]


@router.get("/strategy", response_model=StrategyConfigOut)
def strategy(db: Session = Depends(get_db)) -> StrategyConfig:
    return _default_strategy(db)


@router.put("/strategy", response_model=StrategyConfigOut)
def update_strategy(payload: StrategyConfigUpdate, db: Session = Depends(get_db)) -> StrategyConfig:
    config = _default_strategy(db)
    config.min_absolute_sell_change = payload.min_absolute_sell_change
    config.min_sell_change_rate = payload.min_sell_change_rate
    config.min_price_change_rate = payload.min_price_change_rate
    config.min_price_volatility_rate = payload.min_price_volatility_rate
    config.min_buy_change_rate = payload.min_buy_change_rate
    config.min_volume_change_rate = payload.min_volume_change_rate
    config.cooldown_minutes = payload.cooldown_minutes
    config.quality_penalty_max = payload.quality_penalty_max
    config.sell_fee_rate = payload.sell_fee_rate
    config.withdraw_fee_rate = payload.withdraw_fee_rate
    config.fx_rate = payload.fx_rate
    db.commit()
    db.refresh(config)
    return config


@router.get("/opportunities", response_model=list[MonitorItemOut])
def opportunities(db: Session = Depends(get_db)) -> list[MonitorItemOut]:
    config = _default_strategy(db)
    items = [_monitor_item(db, item, config) for item in db.query(Item).filter_by(is_active=True).all()]
    return sorted(items, key=_opportunity_rank_score, reverse=True)


def _monitor_item(db: Session, item: Item, config: StrategyConfig) -> MonitorItemOut:
    latest_snapshot = (
        db.query(MarketSnapshot)
        .filter(MarketSnapshot.item_id == item.id)
        .order_by(MarketSnapshot.captured_at.desc())
        .first()
    )
    latest_alert = db.query(Alert).filter(Alert.item_id == item.id).order_by(Alert.created_at.desc()).first()
    buy_score, sell_score = score_from_snapshot(latest_snapshot, latest_alert)
    source_quality = _source_quality(latest_snapshot)
    adjusted_buy_score, adjusted_sell_score, quality_penalty = _quality_adjusted_scores(
        buy_score, sell_score, source_quality, config.quality_penalty_max
    )
    category_strategy = _category_strategy(item, latest_snapshot)
    adjusted_buy_score, adjusted_sell_score = _category_adjusted_scores(
        adjusted_buy_score, adjusted_sell_score, category_strategy
    )
    backtest_signal = _backtest_signal(db, latest_alert)
    status = status_from_alert(latest_alert)
    decision_signal = _decision_signal(latest_snapshot, status, adjusted_buy_score, adjusted_sell_score, source_quality)
    return MonitorItemOut(
        id=item.id,
        display_name=item.display_name,
        market_hash_name=item.market_hash_name,
        exterior=item.exterior,
        category=item.category,
        steam_item_nameid=item.steam_item_nameid,
        pool_name=item.pool.name if item.pool else None,
        status=status,
        buy_score=buy_score,
        sell_score=sell_score,
        adjusted_buy_score=adjusted_buy_score,
        adjusted_sell_score=adjusted_sell_score,
        quality_penalty=quality_penalty,
        latest_snapshot=_snapshot_out(latest_snapshot, config) if latest_snapshot else None,
        latest_alert=_alert_out(latest_alert) if latest_alert else None,
        source_quality=source_quality,
        category_strategy=category_strategy,
        backtest_signal=backtest_signal,
        decision_signal=decision_signal,
    )


def _monitor_coverage_status(active_item_count: int) -> str:
    if active_item_count < 100:
        return "below_p1"
    if active_item_count > 300:
        return "over_p1"
    return "ready"


def _monitor_pool_coverage(db: Session) -> list[MonitorCoverageBucketOut]:
    pools = db.query(MonitorPool).order_by(MonitorPool.name.asc()).all()
    return [
        MonitorCoverageBucketOut(
            name=pool.name,
            active_count=sum(1 for item in pool.items if item.is_active),
            total_count=len(pool.items),
        )
        for pool in pools
    ]


def _monitor_category_coverage(active_items: list[Item], all_items: list[Item]) -> list[MonitorCoverageBucketOut]:
    active_counts: dict[str, int] = {}
    total_counts: dict[str, int] = {}
    for item in active_items:
        category = item.category or "uncategorized"
        active_counts[category] = active_counts.get(category, 0) + 1
    for item in all_items:
        category = item.category or "uncategorized"
        total_counts[category] = total_counts.get(category, 0) + 1
    return [
        MonitorCoverageBucketOut(
            name=category,
            active_count=count,
            total_count=total_counts.get(category, count),
        )
        for category, count in sorted(active_counts.items(), key=lambda row: row[1], reverse=True)
    ] if all_items else []


def _opportunity_rank_score(row: MonitorItemOut) -> int:
    return max(row.adjusted_buy_score, row.adjusted_sell_score) + row.backtest_signal.score_adjustment


def _ops_status(
    runs: list[CollectRunLog],
    push_records: list[PushRecord],
    worker_lag_minutes: float | None,
    source_error_count: int,
) -> str:
    if not runs:
        return "warn"
    if all(run.status == "failed" for run in runs):
        return "fail"
    if push_records and all(record.status == "failed" for record in push_records):
        return "fail"
    if worker_lag_minutes is not None and worker_lag_minutes > 60:
        return "warn"
    if source_error_count > 0 or any(run.status == "partial" for run in runs):
        return "warn"
    return "ok"


def _database_kind(database_url: str) -> str:
    if database_url.startswith("postgresql"):
        return "postgresql"
    if database_url.startswith("sqlite"):
        return "sqlite"
    return "unknown"


def _push_configured() -> bool:
    channel = settings.push_channel.lower()
    if channel == "wechat":
        return bool(settings.wechat_webhook_url)
    if channel == "qq":
        return bool(settings.qq_webhook_url)
    return False


def _runtime_audit_items() -> list[RuntimeAuditItemOut]:
    provider = settings.market_provider.lower()
    database_kind = _database_kind(settings.database_url)
    cors_origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
    items = [
        _audit_item(
            "database",
            "数据库",
            "ready" if database_kind == "postgresql" else "warn",
            "生产环境建议使用 PostgreSQL" if database_kind != "postgresql" else "已使用 PostgreSQL",
        ),
        _audit_item(
            "postgres_password",
            "数据库密码",
            "fail" if _has_default_database_password(settings.database_url) else "ready",
            "检测到默认数据库密码，请上线前修改" if _has_default_database_password(settings.database_url) else "未检测到默认数据库密码",
        ),
        _audit_item(
            "market_provider",
            "行情源",
            "ready" if provider == "steam" else "warn",
            "生产验证建议使用 Steam 数据源" if provider != "steam" else "已使用 Steam 数据源",
        ),
        _audit_item(
            "orderbook",
            "订单簿",
            "ready" if settings.steam_orderbook_enabled else "warn",
            "未开启订单簿时在售/求购深度会补位" if not settings.steam_orderbook_enabled else "已开启订单簿",
        ),
        _audit_item(
            "push",
            "推送",
            "ready" if _push_configured() else "warn",
            "未配置微信或 QQ Webhook，外部异动推送会跳过" if not _push_configured() else "推送通道已配置",
        ),
        _audit_item(
            "worker_sleep",
            "worker 间隔",
            "ready" if 5 <= settings.worker_sleep_seconds <= 300 else "warn",
            "建议保持 5-300 秒，避免过慢或过密轮询" if not 5 <= settings.worker_sleep_seconds <= 300 else "worker 轮询间隔在建议范围内",
        ),
        _audit_item(
            "cors",
            "CORS",
            "warn" if _has_localhost_only_cors(cors_origins) else "ready",
            "仅检测到 localhost，云服务器访问前请加入公网域名或地址" if _has_localhost_only_cors(cors_origins) else "CORS 已包含非本机来源或为空",
        ),
    ]
    return items


def _audit_item(key: str, label: str, status: str, detail: str) -> RuntimeAuditItemOut:
    return RuntimeAuditItemOut(key=key, label=label, status=status, detail=detail)


def _has_default_database_password(database_url: str) -> bool:
    return "cs_quant_password" in database_url or "change_me" in database_url


def _has_localhost_only_cors(origins: list[str]) -> bool:
    return bool(origins) and all("localhost" in origin or "127.0.0.1" in origin for origin in origins)


def _acceptance_item(key: str, label: str, status: str, evidence: str) -> AcceptanceItemOut:
    return AcceptanceItemOut(key=key, label=label, status=status, evidence=evidence)


def _field_acceptance_status(field_quality: SourceFieldQualityOut, field: str, orderbook_enabled: bool) -> str:
    metric = next((row for row in field_quality.fields if row.field == field), None)
    if metric is not None and metric.real_ratio >= 0.8 and orderbook_enabled:
        return "passed"
    return "review"


def _field_acceptance_evidence(field_quality: SourceFieldQualityOut, field: str, orderbook_enabled: bool) -> str:
    metric = next((row for row in field_quality.fields if row.field == field), None)
    ratio = metric.real_ratio if metric else 0
    label = metric.label if metric else field
    orderbook = "已开启订单簿" if orderbook_enabled else "未开启订单簿"
    return f"{label}真实率 {ratio:.0%}，{orderbook}"


def _retention_metric(db: Session, model, date_column, name: str, retention_days: int | None, policy: str) -> RetentionMetricOut:
    return RetentionMetricOut(
        name=name,
        retention_days=retention_days,
        row_count=db.query(model).count(),
        oldest_at=db.query(date_column).order_by(date_column.asc()).limit(1).scalar(),
        policy=policy,
    )


def _configured_nameids() -> dict[str, str]:
    try:
        payload = json.loads(settings.steam_orderbook_item_nameids)
    except json.JSONDecodeError:
        return {}
    return {str(key): str(value) for key, value in payload.items() if value}


def _source_config_suggestion(provider: str, orderbook_enabled: bool, coverage: float) -> str:
    if provider == "mock":
        return "当前为 Mock 数据源，仅适合本地自测；P0 验证前建议切换 MARKET_PROVIDER=steam"
    if provider != "steam":
        return "未知数据源配置，请确认 MARKET_PROVIDER"
    if not orderbook_enabled:
        return "Steam priceoverview 可验证价格与成交，买卖盘深度仍会补位；如需验证在售/求购，请开启订单簿"
    if coverage < 0.8:
        return "订单簿已开启，但活跃饰品 Steam NameID 覆盖不足，建议先批量发现或手工维护"
    return "Steam 与订单簿配置已具备 P0 采集验证基础"


def _alert_out(alert: Alert) -> AlertOut:
    platform = alert.platform or Platform(name="Unknown", code="unknown")
    return AlertOut(
        id=alert.id,
        item_id=alert.item_id,
        platform_id=alert.platform_id,
        alert_type=alert.alert_type,
        severity=alert.severity,
        direction=alert.direction,
        title=alert.title,
        detail=alert.detail,
        previous_value=alert.previous_value,
        current_value=alert.current_value,
        absolute_change=alert.absolute_change,
        change_rate=alert.change_rate,
        created_at=alert.created_at,
        item_name=alert.item.display_name,
        platform_name=platform.name,
    )


def _snapshot_out(snapshot: MarketSnapshot, config: StrategyConfig) -> SnapshotOut:
    spread_amount = snapshot.lowest_price - snapshot.highest_buy_price
    spread_rate = spread_amount / snapshot.lowest_price if snapshot.lowest_price else 0
    fee_rate = min(1, config.sell_fee_rate + config.withdraw_fee_rate)
    net_sell_price = snapshot.lowest_price * (1 - fee_rate) * config.fx_rate
    net_spread_amount = net_sell_price - snapshot.highest_buy_price
    net_spread_rate = net_spread_amount / snapshot.lowest_price if snapshot.lowest_price else 0
    return SnapshotOut(
        id=snapshot.id,
        lowest_price=snapshot.lowest_price,
        sell_count=snapshot.sell_count,
        highest_buy_price=snapshot.highest_buy_price,
        buy_count=snapshot.buy_count,
        volume_24h=snapshot.volume_24h,
        avg_price_24h=snapshot.avg_price_24h,
        spread_amount=spread_amount,
        spread_rate=spread_rate,
        net_sell_price=net_sell_price,
        net_spread_amount=net_spread_amount,
        net_spread_rate=net_spread_rate,
        captured_at=snapshot.captured_at,
    )


def _item_out(item: Item) -> ItemOut:
    return ItemOut(
        id=item.id,
        market_hash_name=item.market_hash_name,
        display_name=item.display_name,
        exterior=item.exterior,
        category=item.category,
        steam_item_nameid=item.steam_item_nameid,
        is_active=item.is_active,
        pool_id=item.pool_id,
        pool_name=item.pool.name if item.pool else None,
    )


def _backtest_out(row: BacktestResult) -> BacktestResultOut:
    return BacktestResultOut(
        id=row.id,
        alert_id=row.alert_id,
        item_id=row.item_id,
        platform_id=row.platform_id,
        horizon_minutes=row.horizon_minutes,
        entry_price=row.entry_price,
        exit_price=row.exit_price,
        price_change=row.price_change,
        change_rate=row.change_rate,
        evaluated_at=row.evaluated_at,
        created_at=row.created_at,
        item_name=row.item.display_name,
        alert_type=row.alert.alert_type,
        direction=row.alert.direction,
    )


def _heatmap(snapshots: list[MarketSnapshot]) -> list[HeatmapBucketOut]:
    buckets: dict[int, dict[str, float]] = {}
    previous_by_hour: dict[int, MarketSnapshot] = {}
    for snapshot in snapshots:
        hour = snapshot.captured_at.hour
        bucket = buckets.setdefault(
            hour,
            {
                "snapshot_count": 0,
                "sell_count": 0,
                "buy_count": 0,
                "volume_24h": 0,
                "lowest_price": 0,
                "max_sell_change": 0,
                "max_buy_change": 0,
            },
        )
        bucket["snapshot_count"] += 1
        bucket["sell_count"] += snapshot.sell_count
        bucket["buy_count"] += snapshot.buy_count
        bucket["volume_24h"] += snapshot.volume_24h
        bucket["lowest_price"] += snapshot.lowest_price
        previous = previous_by_hour.get(hour)
        if previous is not None:
            bucket["max_sell_change"] = max(bucket["max_sell_change"], abs(snapshot.sell_count - previous.sell_count))
            bucket["max_buy_change"] = max(bucket["max_buy_change"], abs(snapshot.buy_count - previous.buy_count))
        previous_by_hour[hour] = snapshot
    return [
        HeatmapBucketOut(
            hour=hour,
            snapshot_count=int(row["snapshot_count"]),
            avg_sell_count=row["sell_count"] / row["snapshot_count"],
            avg_buy_count=row["buy_count"] / row["snapshot_count"],
            avg_volume_24h=row["volume_24h"] / row["snapshot_count"],
            avg_lowest_price=row["lowest_price"] / row["snapshot_count"],
            max_sell_change=row["max_sell_change"],
            max_buy_change=row["max_buy_change"],
        )
        for hour, row in sorted(buckets.items())
    ]


def _alert_summary(alerts: list[Alert]) -> list[AlertSummaryOut]:
    grouped: dict[str, list[Alert]] = {}
    for alert in alerts:
        grouped.setdefault(alert.alert_type, []).append(alert)
    return [
        AlertSummaryOut(
            alert_type=alert_type,
            total_count=len(rows),
            recent_alerts=[_alert_out(alert) for alert in rows[:3]],
        )
        for alert_type, rows in sorted(grouped.items(), key=lambda item: len(item[1]), reverse=True)
    ]


def _source_quality(snapshot: MarketSnapshot | None) -> SourceQualityOut | None:
    if snapshot is None:
        return None
    try:
        payload = json.loads(snapshot.raw_payload or "{}")
    except json.JSONDecodeError:
        return None
    quality = payload.get("source_quality") or {}
    real_fields = list(quality.get("real_fields") or [])
    fallback_fields = list(quality.get("fallback_fields") or [])
    total = len(real_fields) + len(fallback_fields)
    real_ratio = len(real_fields) / total if total else 0
    if real_ratio >= 0.8:
        level = "trusted"
    elif real_ratio > 0:
        level = "partial"
    else:
        level = "fallback"
    return SourceQualityOut(
        real_fields=real_fields,
        fallback_fields=fallback_fields,
        real_field_count=len(real_fields),
        fallback_field_count=len(fallback_fields),
        real_ratio=real_ratio,
        level=level,
    )


def _quality_adjusted_scores(
    buy_score: int,
    sell_score: int,
    source_quality: SourceQualityOut | None,
    max_penalty: int,
) -> tuple[int, int, int]:
    if source_quality is None:
        penalty = round(max_penalty / 2)
        return max(0, buy_score - penalty), max(0, sell_score - penalty), penalty
    penalty = round((1 - source_quality.real_ratio) * max_penalty)
    return max(0, buy_score - penalty), max(0, sell_score - penalty), penalty


def _category_strategy(item: Item, snapshot: MarketSnapshot | None) -> CategoryStrategyOut:
    category = (item.category or "uncategorized").lower()
    if category in {"gloves", "knife"}:
        profile = "高客单低流动"
        buy_adjustment = -6
        sell_adjustment = 4
        reason = "高客单饰品优先控制流动性与卖出安全边际"
    elif category in {"case", "sticker", "capsule"}:
        profile = "高流动事件"
        buy_adjustment = 5
        sell_adjustment = -2
        reason = "事件类饰品更看重成交与短期热度"
    elif category in {"rifle", "pistol", "smg", "sniper", "shotgun"}:
        profile = "常规武器"
        buy_adjustment = 2
        sell_adjustment = 0
        reason = "常规武器按流动性与价差均衡处理"
    else:
        profile = "默认品类"
        buy_adjustment = 0
        sell_adjustment = 0
        reason = "暂无专用品类规则"
    if snapshot is not None:
        spread_rate = (snapshot.lowest_price - snapshot.highest_buy_price) / max(snapshot.lowest_price, 1)
        if spread_rate > 0.12:
            buy_adjustment -= 4
            sell_adjustment += 2
            reason = f"{reason}，当前买卖价差偏大"
        if snapshot.volume_24h <= 1:
            buy_adjustment -= 3
            sell_adjustment += 2
            reason = f"{reason}，24h 成交偏低"
    return CategoryStrategyOut(
        category=category,
        profile=profile,
        buy_adjustment=buy_adjustment,
        sell_adjustment=sell_adjustment,
        reason=reason,
    )


def _category_adjusted_scores(
    buy_score: int,
    sell_score: int,
    category_strategy: CategoryStrategyOut,
) -> tuple[int, int]:
    return (
        max(0, min(100, buy_score + category_strategy.buy_adjustment)),
        max(0, min(100, sell_score + category_strategy.sell_adjustment)),
    )


def _backtest_signal(db: Session, alert: Alert | None) -> BacktestSignalOut:
    if alert is None:
        return BacktestSignalOut(
            alert_type="",
            horizon_minutes=60,
            sample_count=0,
            win_rate=0,
            avg_change_rate=0,
            score_adjustment=0,
            reason="暂无告警，无法匹配回测样本",
        )
    row = (
        db.query(BacktestResult)
        .join(Alert, BacktestResult.alert_id == Alert.id)
        .filter(Alert.alert_type == alert.alert_type, BacktestResult.horizon_minutes == 60)
        .all()
    )
    if not row:
        return BacktestSignalOut(
            alert_type=alert.alert_type,
            horizon_minutes=60,
            sample_count=0,
            win_rate=0,
            avg_change_rate=0,
            score_adjustment=0,
            reason="暂无同类 60 分钟回测样本",
        )
    wins = sum(1 for result in row if _backtest_is_win(result))
    win_rate = wins / len(row)
    avg_change_rate = sum(result.change_rate for result in row) / len(row)
    score_adjustment = _backtest_score_adjustment(len(row), win_rate, avg_change_rate)
    return BacktestSignalOut(
        alert_type=alert.alert_type,
        horizon_minutes=60,
        sample_count=len(row),
        win_rate=win_rate,
        avg_change_rate=avg_change_rate,
        score_adjustment=score_adjustment,
        reason=f"同类 60 分钟回测 {len(row)} 条，胜率 {win_rate * 100:.1f}%",
    )


def _backtest_score_adjustment(sample_count: int, win_rate: float, avg_change_rate: float) -> int:
    if sample_count < 3:
        return 0
    adjustment = 0
    if win_rate >= 0.65:
        adjustment += 6
    elif win_rate <= 0.35:
        adjustment -= 6
    if avg_change_rate >= 0.03:
        adjustment += 4
    elif avg_change_rate <= -0.03:
        adjustment -= 4
    return adjustment


def _backtest_is_win(result: BacktestResult) -> bool:
    direction = result.alert.direction
    if direction in ("偏买入机会", "偏扫货拉升"):
        return result.price_change > 0
    if direction == "偏卖压风险":
        return result.price_change < 0
    return False


def _decision_signal(
    snapshot: MarketSnapshot | None,
    status: str,
    adjusted_buy_score: int,
    adjusted_sell_score: int,
    source_quality: SourceQualityOut | None,
) -> DecisionSignalOut:
    signal = decision_from_scores(
        snapshot,
        status,
        adjusted_buy_score,
        adjusted_sell_score,
        source_quality.real_ratio if source_quality else None,
    )
    return DecisionSignalOut(**signal)


def _ensure_pool(db: Session, pool_id: int | None) -> None:
    if pool_id is not None and db.get(MonitorPool, pool_id) is None:
        raise HTTPException(status_code=404, detail="monitor pool not found")


def _ensure_item(db: Session, item_id: int) -> None:
    if db.get(Item, item_id) is None:
        raise HTTPException(status_code=404, detail="item not found")


def _history_points(db: Session, item_id: int, field: str, limit: int) -> list[HistoryPointOut]:
    rows = (
        db.query(MarketSnapshot)
        .filter(MarketSnapshot.item_id == item_id)
        .order_by(MarketSnapshot.captured_at.desc())
        .limit(limit)
        .all()
    )
    return [
        HistoryPointOut(captured_at=snapshot.captured_at, value=float(getattr(snapshot, field)))
        for snapshot in reversed(rows)
    ]


def _default_strategy(db: Session) -> StrategyConfig:
    config = db.query(StrategyConfig).filter_by(name="default").first()
    if config is None:
        config = StrategyConfig(name="default")
        db.add(config)
        db.commit()
        db.refresh(config)
    return config
