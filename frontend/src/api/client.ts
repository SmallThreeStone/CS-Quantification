import type {
  Alert,
  ItemDetail,
  ManagedItem,
  ManagedItemInput,
  MonitorItem,
  PushRecord,
  StrategyConfig,
  StrategyConfigUpdate
} from "../types";

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
  items: () => request<ManagedItem[]>("/api/items"),
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
