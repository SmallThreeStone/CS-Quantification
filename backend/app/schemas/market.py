from datetime import datetime

from pydantic import BaseModel, Field


class SnapshotOut(BaseModel):
    id: int
    lowest_price: float
    sell_count: int
    highest_buy_price: float
    buy_count: int
    volume_24h: int
    avg_price_24h: float
    spread_amount: float
    spread_rate: float
    net_sell_price: float
    net_spread_amount: float
    net_spread_rate: float
    captured_at: datetime


class HistoryPointOut(BaseModel):
    captured_at: datetime
    value: float


class SourceQualityOut(BaseModel):
    real_fields: list[str]
    fallback_fields: list[str]
    real_field_count: int
    fallback_field_count: int
    real_ratio: float
    level: str


class DecisionSignalOut(BaseModel):
    action: str
    confidence: int
    reason: str


class CategoryStrategyOut(BaseModel):
    category: str
    profile: str
    buy_adjustment: int
    sell_adjustment: int
    reason: str


class BacktestSignalOut(BaseModel):
    alert_type: str
    horizon_minutes: int
    sample_count: int
    win_rate: float
    avg_change_rate: float
    score_adjustment: int
    reason: str


class AlertOut(BaseModel):
    id: int
    item_id: int
    platform_id: int
    alert_type: str
    severity: str
    direction: str
    title: str
    detail: str
    previous_value: float
    current_value: float
    absolute_change: float
    change_rate: float
    created_at: datetime
    item_name: str
    platform_name: str


class PushRecordOut(BaseModel):
    id: int
    alert_id: int
    channel: str
    status: str
    target: str
    error: str
    created_at: datetime
    sent_at: datetime | None

    model_config = {"from_attributes": True}


class BacktestResultOut(BaseModel):
    id: int
    alert_id: int
    item_id: int
    platform_id: int
    horizon_minutes: int
    entry_price: float
    exit_price: float
    price_change: float
    change_rate: float
    evaluated_at: datetime
    created_at: datetime
    item_name: str
    alert_type: str
    direction: str


class BacktestSummaryOut(BaseModel):
    alert_type: str
    horizon_minutes: int
    sample_count: int
    win_count: int
    win_rate: float
    avg_change_rate: float
    max_gain_rate: float
    max_drawdown_rate: float
    profit_loss_ratio: float
    confidence_level: str


class TuningSuggestionOut(BaseModel):
    alert_type: str
    horizon_minutes: int
    sample_count: int
    action: str
    parameter_hint: str
    reason: str


class HeatmapBucketOut(BaseModel):
    hour: int
    snapshot_count: int
    avg_sell_count: float
    avg_buy_count: float
    avg_volume_24h: float
    avg_lowest_price: float
    max_sell_change: float
    max_buy_change: float


class AlertSummaryOut(BaseModel):
    alert_type: str
    total_count: int
    recent_alerts: list[AlertOut]


class CollectRunLogOut(BaseModel):
    id: int
    mode: str
    provider: str
    status: str
    item_count: int
    snapshot_count: int
    alert_count: int
    error_count: int
    real_field_count: int
    fallback_field_count: int
    fallback_count: int
    duration_ms: int
    error: str
    started_at: datetime
    finished_at: datetime | None

    model_config = {"from_attributes": True}


class StrategyConfigOut(BaseModel):
    id: int
    name: str
    min_absolute_sell_change: int
    min_sell_change_rate: float
    min_price_change_rate: float
    min_price_volatility_rate: float
    min_buy_change_rate: float
    min_volume_change_rate: float
    cooldown_minutes: int
    quality_penalty_max: int
    sell_fee_rate: float
    withdraw_fee_rate: float
    fx_rate: float

    model_config = {"from_attributes": True}


class StrategyConfigUpdate(BaseModel):
    min_absolute_sell_change: int = Field(ge=1, le=10000)
    min_sell_change_rate: float = Field(ge=0.01, le=5)
    min_price_change_rate: float = Field(ge=0.001, le=1)
    min_price_volatility_rate: float = Field(ge=0.001, le=1)
    min_buy_change_rate: float = Field(ge=0.01, le=5)
    min_volume_change_rate: float = Field(ge=0.01, le=10)
    cooldown_minutes: int = Field(ge=0, le=1440)
    quality_penalty_max: int = Field(ge=0, le=100)
    sell_fee_rate: float = Field(ge=0, le=0.5)
    withdraw_fee_rate: float = Field(ge=0, le=0.5)
    fx_rate: float = Field(ge=0.01, le=100)


class ItemOut(BaseModel):
    id: int
    market_hash_name: str
    display_name: str
    exterior: str
    category: str
    steam_item_nameid: str
    is_active: bool
    pool_id: int | None
    pool_name: str | None = None

    model_config = {"from_attributes": True}


class ItemCreate(BaseModel):
    market_hash_name: str = Field(min_length=3, max_length=240)
    display_name: str = Field(min_length=1, max_length=160)
    exterior: str = Field(default="", max_length=80)
    category: str = Field(default="", max_length=80)
    steam_item_nameid: str = Field(default="", max_length=80)
    is_active: bool = True
    pool_id: int | None = None


class ItemUpdate(BaseModel):
    market_hash_name: str = Field(min_length=3, max_length=240)
    display_name: str = Field(min_length=1, max_length=160)
    exterior: str = Field(default="", max_length=80)
    category: str = Field(default="", max_length=80)
    steam_item_nameid: str = Field(default="", max_length=80)
    is_active: bool = True
    pool_id: int | None = None


class SteamNameIdOut(BaseModel):
    item_id: int
    market_hash_name: str
    steam_item_nameid: str


class SteamOrderbookValidationOut(BaseModel):
    item_id: int
    market_hash_name: str
    steam_item_nameid: str
    ok: bool
    sell_count: int = 0
    buy_count: int = 0
    highest_buy_price: float = 0
    error: str = ""


class SteamNameIdBatchOut(BaseModel):
    total: int
    success_count: int
    failure_count: int
    results: list[SteamOrderbookValidationOut]


class MonitorPoolOut(BaseModel):
    id: int
    name: str
    interval_minutes: int
    description: str
    last_collected_at: datetime | None
    active_item_count: int


class MonitorPoolCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    interval_minutes: int = Field(ge=1, le=1440)
    description: str = Field(default="", max_length=240)


class MonitorPoolUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    interval_minutes: int = Field(ge=1, le=1440)
    description: str = Field(default="", max_length=240)


class MonitorItemOut(BaseModel):
    id: int
    display_name: str
    market_hash_name: str
    exterior: str
    category: str
    steam_item_nameid: str
    pool_name: str | None
    status: str
    buy_score: int
    sell_score: int
    adjusted_buy_score: int
    adjusted_sell_score: int
    quality_penalty: int
    latest_snapshot: SnapshotOut | None
    latest_alert: AlertOut | None
    source_quality: SourceQualityOut | None
    category_strategy: CategoryStrategyOut
    backtest_signal: BacktestSignalOut
    decision_signal: DecisionSignalOut


class ItemDetailOut(BaseModel):
    id: int
    display_name: str
    market_hash_name: str
    exterior: str
    category: str
    steam_item_nameid: str
    status: str
    buy_score: int
    sell_score: int
    adjusted_buy_score: int
    adjusted_sell_score: int
    quality_penalty: int
    snapshots: list[SnapshotOut]
    alerts: list[AlertOut]
    heatmap: list[HeatmapBucketOut]
    alert_summary: list[AlertSummaryOut]
    source_quality: SourceQualityOut | None
    category_strategy: CategoryStrategyOut
    backtest_signal: BacktestSignalOut
    decision_signal: DecisionSignalOut


class HealthOut(BaseModel):
    status: str
    service: str
    version: str


class OpsHealthOut(BaseModel):
    status: str
    latest_run_status: str
    latest_run_at: datetime | None
    collect_success_rate: float
    push_success_rate: float
    snapshot_count_24h: int
    alert_count_24h: int
    source_error_count_24h: int
    real_field_ratio_24h: float
    worker_lag_minutes: float | None


class OpsReadinessOut(BaseModel):
    ready_for_7d_review: bool
    observed_days: float
    collect_run_count: int
    success_run_count: int
    collect_success_rate: float
    monitored_item_count: int
    items_with_snapshots: int
    snapshot_coverage_rate: float
    snapshot_count: int
    latest_run_at: datetime | None


class FieldQualityOut(BaseModel):
    field: str
    label: str
    real_count: int
    fallback_count: int
    real_ratio: float


class SourceFieldQualityOut(BaseModel):
    snapshot_sample_count: int
    fields: list[FieldQualityOut]


class SourceConfigOut(BaseModel):
    provider: str
    steam_orderbook_enabled: bool
    configured_nameid_count: int
    active_item_count: int
    active_nameid_count: int
    active_nameid_coverage_rate: float
    readiness: str
    suggestion: str


class P0SummaryOut(BaseModel):
    ready: bool
    status: str
    blockers: list[str]
    review_items: list[str]
    readiness: OpsReadinessOut
    source_config: SourceConfigOut
    field_quality: SourceFieldQualityOut
    alert_count: int


class RetentionMetricOut(BaseModel):
    name: str
    retention_days: int | None
    row_count: int
    oldest_at: datetime | None
    policy: str


class RetentionOut(BaseModel):
    snapshot_retention_days: int
    collect_log_retention_days: int
    alert_retention_days: int | None
    backtest_retention_days: int | None
    metrics: list[RetentionMetricOut]


class RetentionCleanupOut(BaseModel):
    snapshot_retention_days: int
    collect_log_retention_days: int
    deleted_snapshots: int
    deleted_collect_logs: int
