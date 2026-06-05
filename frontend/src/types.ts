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
  decision_signal: DecisionSignal;
};

export type ItemDetail = MonitorItem & {
  snapshots: Snapshot[];
  alerts: Alert[];
  heatmap: HeatmapBucket[];
  alert_summary: AlertSummary[];
};
