import type {
  Alert,
  BacktestResult,
  BacktestSummary,
  CollectRun,
  ItemDetail,
  ManagedItem,
  ManagedItemInput,
  MonitorPool,
  MonitorPoolInput,
  MonitorItem,
  OpsHealth,
  OpsReadiness,
  PushRecord,
  Retention,
  RetentionCleanup,
  SourceConfig,
  SourceFieldQuality,
  StrategyConfig,
  StrategyConfigUpdate,
  TuningSuggestion
} from "../types";

const API_BASE = "";

type SteamNameIdBatchResult = {
  total: number;
  success_count: number;
  failure_count: number;
  results: Array<{
    item_id: number;
    market_hash_name: string;
    steam_item_nameid: string;
    ok: boolean;
    sell_count: number;
    buy_count: number;
    highest_buy_price: number;
    error: string;
  }>;
};

export type AlertFilters = {
  item?: string;
  alert_type?: string;
  severity?: string;
  platform?: string;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, init);
  if (!response.ok) {
    throw new Error(`API ${path} failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  health: () => request<{ status: string; service: string; version: string }>("/api/health"),
  opsHealth: () => request<OpsHealth>("/api/ops/health"),
  opsReadiness: () => request<OpsReadiness>("/api/ops/readiness"),
  sourceConfig: () => request<SourceConfig>("/api/source/config"),
  sourceFieldQuality: () => request<SourceFieldQuality>("/api/source/field-quality"),
  retention: () => request<Retention>("/api/retention"),
  cleanupRetention: () => request<RetentionCleanup>("/api/retention/cleanup", { method: "POST" }),
  collect: () => request<Alert[]>("/api/collect", { method: "POST" }),
  collectRuns: () => request<CollectRun[]>("/api/collect-runs"),
  monitor: () => request<MonitorItem[]>("/api/monitor"),
  alerts: (filters: AlertFilters = {}) => request<Alert[]>(queryPath("/api/alerts", filters)),
  backtests: () => request<BacktestResult[]>("/api/backtests"),
  backtestSummary: () => request<BacktestSummary[]>("/api/backtests/summary"),
  tuningSuggestions: () => request<TuningSuggestion[]>("/api/backtests/tuning-suggestions"),
  evaluateBacktests: () => request<BacktestResult[]>("/api/backtests/evaluate", { method: "POST" }),
  pushRecords: () => request<PushRecord[]>("/api/push-records"),
  items: () => request<ManagedItem[]>("/api/items"),
  monitorPools: () => request<MonitorPool[]>("/api/monitor-pools"),
  createMonitorPool: (payload: MonitorPoolInput) =>
    request<MonitorPool>("/api/monitor-pools", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    }),
  updateMonitorPool: (id: number, payload: MonitorPoolInput) =>
    request<MonitorPool>(`/api/monitor-pools/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    }),
  createItem: (payload: ManagedItemInput) =>
    request<ManagedItem>("/api/items", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    }),
  updateItem: (id: number, payload: ManagedItemInput) =>
    request<ManagedItem>(`/api/items/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    }),
  setItemActive: (id: number, isActive: boolean) =>
    request<ManagedItem>(`/api/items/${id}/active?is_active=${isActive}`, { method: "PATCH" }),
  discoverSteamNameId: (id: number) =>
    request<{ item_id: number; market_hash_name: string; steam_item_nameid: string }>(
      `/api/items/${id}/steam-nameid/discover`,
      { method: "POST" }
    ),
  validateSteamNameId: (id: number) =>
    request<{
      item_id: number;
      market_hash_name: string;
      steam_item_nameid: string;
      ok: boolean;
      sell_count: number;
      buy_count: number;
      highest_buy_price: number;
      error: string;
    }>(`/api/items/${id}/steam-nameid/validate`, { method: "POST" }),
  discoverMissingSteamNameIds: () =>
    request<SteamNameIdBatchResult>("/api/steam-nameids/discover-missing", { method: "POST" }),
  validateAllSteamNameIds: () => request<SteamNameIdBatchResult>("/api/steam-nameids/validate-all", { method: "POST" }),
  strategy: () => request<StrategyConfig>("/api/strategy"),
  updateStrategy: (payload: StrategyConfigUpdate) =>
    request<StrategyConfig>("/api/strategy", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    }),
  opportunities: () => request<MonitorItem[]>("/api/opportunities"),
  item: (id: number) => request<ItemDetail>(`/api/items/${id}`)
};

function queryPath(path: string, params: Record<string, string | undefined>) {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value) {
      search.set(key, value);
    }
  });
  const suffix = search.toString();
  return suffix ? `${path}?${suffix}` : path;
}
