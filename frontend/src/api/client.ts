import type { Alert, ItemDetail, MonitorItem, PushRecord, StrategyConfig, StrategyConfigUpdate } from "../types";

const API_BASE = "";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, init);
  if (!response.ok) {
    throw new Error(`API ${path} failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  health: () => request<{ status: string; service: string; version: string }>("/api/health"),
  collect: () => request<Alert[]>("/api/collect", { method: "POST" }),
  monitor: () => request<MonitorItem[]>("/api/monitor"),
  alerts: () => request<Alert[]>("/api/alerts"),
  pushRecords: () => request<PushRecord[]>("/api/push-records"),
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
