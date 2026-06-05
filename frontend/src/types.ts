export type Snapshot = {
  id: number;
  lowest_price: number;
  sell_count: number;
  highest_buy_price: number;
  buy_count: number;
  volume_24h: number;
  avg_price_24h: number;
  captured_at: string;
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
  min_buy_change_rate: number;
  cooldown_minutes: number;
};

export type StrategyConfigUpdate = Omit<StrategyConfig, "id" | "name">;

export type ManagedItem = {
  id: number;
  market_hash_name: string;
  display_name: string;
  exterior: string;
  category: string;
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

export type MonitorItem = {
  id: number;
  display_name: string;
  market_hash_name: string;
  exterior: string;
  category: string;
  pool_name: string | null;
  status: string;
  buy_score: number;
  sell_score: number;
  latest_snapshot: Snapshot | null;
  latest_alert: Alert | null;
};

export type ItemDetail = MonitorItem & {
  snapshots: Snapshot[];
  alerts: Alert[];
};
