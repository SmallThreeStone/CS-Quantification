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

export type MonitorItem = {
  id: number;
  display_name: string;
  market_hash_name: string;
  exterior: string;
  category: string;
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
