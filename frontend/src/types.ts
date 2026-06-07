export type Snapshot = {
  id: number;
  lowest_price: number;
  sell_count: number;
  highest_buy_price: number;
  buy_count: number;
  volume_24h: number;
  avg_price_24h: number;
  spread_amount: number;
  spread_rate: number;
  net_sell_price: number;
  net_spread_amount: number;
  net_spread_rate: number;
  captured_at: string;
};

export type SourceQuality = {
  real_fields: string[];
  fallback_fields: string[];
  real_field_count: number;
  fallback_field_count: number;
  real_ratio: number;
  level: "trusted" | "partial" | "fallback";
};

export type DecisionSignal = {
  action: "买入" | "持有" | "卖出" | "观望";
  confidence: number;
  reason: string;
};

export type CategoryStrategy = {
  category: string;
  profile: string;
  buy_adjustment: number;
  sell_adjustment: number;
  reason: string;
};

export type BacktestSignal = {
  alert_type: string;
  horizon_minutes: number;
  sample_count: number;
  win_rate: number;
  avg_change_rate: number;
  score_adjustment: number;
  reason: string;
};

export type Alert = {
  id: number;
  item_id: number;
  platform_id: number;
  alert_type: string;
  severity: string;
  direction: string;
  title: string;
  detail: string;
  previous_value: number;
  current_value: number;
  absolute_change: number;
  change_rate: number;
  created_at: string;
  item_name: string;
  platform_name: string;
};

export type AlertTypeCoverage = {
  alert_type: string;
  count: number;
};

export type AlertCoverage = {
  total_count: number;
  recent_24h_count: number;
  covered_type_count: number;
  expected_type_count: number;
  traceable_count: number;
  traceable_rate: number;
  latest_alert: Alert | null;
  types: AlertTypeCoverage[];
};

export type PushRecord = {
  id: number;
  alert_id: number;
  channel: string;
  status: string;
  target: string;
  error: string;
  created_at: string;
  sent_at: string | null;
};

export type BacktestResult = {
  id: number;
  alert_id: number;
  item_id: number;
  platform_id: number;
  horizon_minutes: number;
  entry_price: number;
  exit_price: number;
  price_change: number;
  change_rate: number;
  evaluated_at: string;
  created_at: string;
  item_name: string;
  alert_type: string;
  direction: string;
};

export type BacktestSummary = {
  alert_type: string;
  horizon_minutes: number;
  sample_count: number;
  win_count: number;
  win_rate: number;
  avg_change_rate: number;
  max_gain_rate: number;
  max_drawdown_rate: number;
  profit_loss_ratio: number;
  confidence_level: string;
};

export type TuningSuggestion = {
  alert_type: string;
  horizon_minutes: number;
  sample_count: number;
  action: string;
  parameter_hint: string;
  reason: string;
};

export type HeatmapBucket = {
  hour: number;
  snapshot_count: number;
  avg_sell_count: number;
  avg_buy_count: number;
  avg_volume_24h: number;
  avg_lowest_price: number;
  max_sell_change: number;
  max_buy_change: number;
};

export type AlertSummary = {
  alert_type: string;
  total_count: number;
  recent_alerts: Alert[];
};

export type CollectRun = {
  id: number;
  mode: string;
  provider: string;
  status: string;
  item_count: number;
  snapshot_count: number;
  alert_count: number;
  error_count: number;
  real_field_count: number;
  fallback_field_count: number;
  fallback_count: number;
  duration_ms: number;
  error: string;
  started_at: string;
  finished_at: string | null;
};

export type OpsHealth = {
  status: "ok" | "warn" | "fail";
  latest_run_status: string;
  latest_run_at: string | null;
  collect_success_rate: number;
  push_success_rate: number;
  snapshot_count_24h: number;
  alert_count_24h: number;
  source_error_count_24h: number;
  real_field_ratio_24h: number;
  worker_lag_minutes: number | null;
};

export type ApiLatency = {
  status: "ok" | "warn" | "fail";
  window_minutes: number;
  request_count: number;
  avg_latency_ms: number;
  p95_latency_ms: number;
  max_latency_ms: number;
  slow_request_count: number;
  error_count: number;
  latest_path: string | null;
  latest_status_code: number | null;
  latest_at: string | null;
};

export type DbWriteVolumeMetric = {
  name: string;
  table: string;
  total_count: number;
  recent_24h_count: number;
  oldest_at: string | null;
  latest_at: string | null;
};

export type DbWriteVolume = {
  status: "active" | "idle";
  window_hours: number;
  total_recent_24h_count: number;
  total_row_count: number;
  latest_write_at: string | null;
  metrics: DbWriteVolumeMetric[];
};

export type HostResource = {
  status: "ok" | "warn" | "fail";
  cpu_percent: number | null;
  memory_total_mb: number | null;
  memory_used_mb: number | null;
  memory_percent: number | null;
  disk_total_gb: number | null;
  disk_used_gb: number | null;
  disk_percent: number | null;
  checked_at: string;
};

export type BackupStatusMetric = {
  key: string;
  label: string;
  status: "ready" | "warn" | "fail";
  script_exists: boolean;
  directory_exists: boolean;
  file_count: number;
  latest_file: string | null;
  latest_size_bytes: number | null;
  latest_at: string | null;
  retention_days: number;
  stale_days: number | null;
  detail: string;
};

export type BackupStatus = {
  status: "ready" | "warn" | "fail";
  checked_at: string;
  metrics: BackupStatusMetric[];
};

export type OpsReadiness = {
  ready_for_7d_review: boolean;
  observed_days: number;
  collect_run_count: number;
  success_run_count: number;
  collect_success_rate: number;
  monitored_item_count: number;
  items_with_snapshots: number;
  snapshot_coverage_rate: number;
  snapshot_count: number;
  latest_run_at: string | null;
};

export type RuntimeConfig = {
  version: string;
  database_kind: string;
  market_provider: string;
  steam_orderbook_enabled: boolean;
  worker_sleep_seconds: number;
  push_channel: string;
  push_configured: boolean;
  cors_origin_count: number;
};

export type RuntimeAuditItem = {
  key: string;
  label: string;
  status: "ready" | "warn" | "fail";
  detail: string;
};

export type RuntimeAudit = {
  status: "ready" | "warn" | "fail";
  fail_count: number;
  warn_count: number;
  items: RuntimeAuditItem[];
};

export type AcceptanceItem = {
  key: string;
  label: string;
  status: "passed" | "review" | "blocked";
  evidence: string;
};

export type Acceptance = {
  status: "passed" | "review" | "blocked";
  passed_count: number;
  review_count: number;
  blocked_count: number;
  items: AcceptanceItem[];
};

export type MvpScopeItem = {
  key: string;
  label: string;
  status: "ready" | "review";
  evidence: string;
};

export type MvpScope = {
  status: "ready" | "review";
  ready_count: number;
  review_count: number;
  item_count: number;
  items: MvpScopeItem[];
};

export type MonitorCoverageBucket = {
  name: string;
  active_count: number;
  total_count: number;
};

export type MonitorCoverage = {
  status: "ready" | "below_p1" | "over_p1";
  active_item_count: number;
  total_item_count: number;
  p1_min_item_count: number;
  p1_max_item_count: number;
  missing_nameid_count: number;
  pools: MonitorCoverageBucket[];
  categories: MonitorCoverageBucket[];
};

export type SteamNameIdTodoItem = {
  item_id: number;
  display_name: string;
  market_hash_name: string;
  pool_name: string | null;
  category: string;
};

export type SteamNameIdTodo = {
  status: "ready" | "partial" | "missing";
  active_item_count: number;
  missing_count: number;
  coverage_rate: number;
  discoverable_count: number;
  pools: MonitorCoverageBucket[];
  missing_items: SteamNameIdTodoItem[];
};

export type FieldQuality = {
  field: string;
  label: string;
  real_count: number;
  fallback_count: number;
  real_ratio: number;
};

export type SourceFieldQuality = {
  snapshot_sample_count: number;
  fields: FieldQuality[];
};

export type SourceConfig = {
  provider: string;
  steam_orderbook_enabled: boolean;
  configured_nameid_count: number;
  active_item_count: number;
  active_nameid_count: number;
  active_nameid_coverage_rate: number;
  readiness: string;
  suggestion: string;
};

export type P0Summary = {
  ready: boolean;
  status: string;
  blockers: string[];
  review_items: string[];
  readiness: OpsReadiness;
  source_config: SourceConfig;
  field_quality: SourceFieldQuality;
  alert_count: number;
};

export type RetentionMetric = {
  name: string;
  retention_days: number | null;
  row_count: number;
  oldest_at: string | null;
  policy: string;
};

export type Retention = {
  snapshot_retention_days: number;
  collect_log_retention_days: number;
  alert_retention_days: number | null;
  backtest_retention_days: number | null;
  metrics: RetentionMetric[];
};

export type RetentionCleanup = {
  snapshot_retention_days: number;
  collect_log_retention_days: number;
  deleted_snapshots: number;
  deleted_collect_logs: number;
};

export type StrategyConfig = {
  id: number;
  name: string;
  min_absolute_sell_change: number;
  min_sell_change_rate: number;
  min_price_change_rate: number;
  min_price_volatility_rate: number;
  min_buy_change_rate: number;
  min_volume_change_rate: number;
  cooldown_minutes: number;
  quality_penalty_max: number;
  sell_fee_rate: number;
  withdraw_fee_rate: number;
  fx_rate: number;
};

export type StrategyConfigUpdate = Omit<StrategyConfig, "id" | "name">;

export type ManagedItem = {
  id: number;
  market_hash_name: string;
  display_name: string;
  exterior: string;
  category: string;
  steam_item_nameid: string;
  is_active: boolean;
  pool_id: number | null;
  pool_name: string | null;
};

export type ManagedItemInput = Omit<ManagedItem, "id" | "pool_name">;

export type MonitorPool = {
  id: number;
  name: string;
  interval_minutes: number;
  description: string;
  last_collected_at: string | null;
  active_item_count: number;
};

export type MonitorPoolInput = Omit<MonitorPool, "id" | "last_collected_at" | "active_item_count">;

export type MonitorItem = {
  id: number;
  display_name: string;
  market_hash_name: string;
  exterior: string;
  category: string;
  steam_item_nameid: string;
  pool_name: string | null;
  status: string;
  buy_score: number;
  sell_score: number;
  adjusted_buy_score: number;
  adjusted_sell_score: number;
  quality_penalty: number;
  latest_snapshot: Snapshot | null;
  latest_alert: Alert | null;
  source_quality: SourceQuality | null;
  category_strategy: CategoryStrategy;
  backtest_signal: BacktestSignal;
  decision_signal: DecisionSignal;
};

export type ItemDetail = MonitorItem & {
  snapshots: Snapshot[];
  alerts: Alert[];
  heatmap: HeatmapBucket[];
  alert_summary: AlertSummary[];
};
