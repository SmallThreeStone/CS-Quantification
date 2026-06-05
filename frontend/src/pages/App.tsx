import { Activity, Bell, Database, Gauge, RefreshCw, Settings, Target } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { api } from "../api/client";
import { AlertList } from "../components/AlertList";
import { Metric } from "../components/Metric";
import { MiniChart } from "../components/MiniChart";
import type { Alert, ItemDetail, MonitorItem } from "../types";

type Tab = "monitor" | "detail" | "alerts" | "opportunities" | "settings" | "source";

export default function App() {
  const [tab, setTab] = useState<Tab>("monitor");
  const [items, setItems] = useState<MonitorItem[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [detail, setDetail] = useState<ItemDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const selected = useMemo(() => items.find((item) => item.id === selectedId) ?? items[0], [items, selectedId]);

  async function refresh() {
    setLoading(true);
    try {
      const [nextItems, nextAlerts] = await Promise.all([api.monitor(), api.alerts()]);
      setItems(nextItems);
      setAlerts(nextAlerts);
      if (!selectedId && nextItems[0]) {
        setSelectedId(nextItems[0].id);
      }
    } finally {
      setLoading(false);
    }
  }

  async function collect() {
    setLoading(true);
    try {
      await api.collect();
      await refresh();
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  useEffect(() => {
    if (!selected?.id) {
      return;
    }
    api.item(selected.id).then(setDetail).catch(() => setDetail(null));
  }, [selected?.id]);

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <Gauge size={24} />
          <div>
            <strong>CS Quant</strong>
            <span>饰品监控盘</span>
          </div>
        </div>
        <nav>
          <button className={tab === "monitor" ? "active" : ""} onClick={() => setTab("monitor")}>
            <Activity size={18} /> 监控总览
          </button>
          <button className={tab === "detail" ? "active" : ""} onClick={() => setTab("detail")}>
            <Target size={18} /> 饰品详情
          </button>
          <button className={tab === "alerts" ? "active" : ""} onClick={() => setTab("alerts")}>
            <Bell size={18} /> 异动告警
          </button>
          <button className={tab === "opportunities" ? "active" : ""} onClick={() => setTab("opportunities")}>
            <Gauge size={18} /> 机会榜
          </button>
          <button className={tab === "settings" ? "active" : ""} onClick={() => setTab("settings")}>
            <Settings size={18} /> 策略配置
          </button>
          <button className={tab === "source" ? "active" : ""} onClick={() => setTab("source")}>
            <Database size={18} /> 数据源状态
          </button>
        </nav>
      </aside>

      <main>
        <header className="topbar">
          <div>
            <h1>{title(tab)}</h1>
            <p>重点池：超导体、清凉薄荷 · 数据源：Steam 适配层 / Mock 回退</p>
          </div>
          <div className="actions">
            <button onClick={refresh} disabled={loading}>
              <RefreshCw size={16} /> 刷新
            </button>
            <button className="primary" onClick={collect} disabled={loading}>
              <Activity size={16} /> 采集一轮
            </button>
          </div>
        </header>

        {tab === "monitor" && <MonitorView items={items} selectedId={selected?.id} onSelect={setSelectedId} />}
        {tab === "detail" && <DetailView detail={detail} />}
        {tab === "alerts" && <AlertList alerts={alerts} />}
        {tab === "opportunities" && <OpportunityView items={items} onSelect={setSelectedId} setTab={setTab} />}
        {tab === "settings" && <SettingsView />}
        {tab === "source" && <SourceView items={items} alerts={alerts} />}
      </main>
    </div>
  );
}

function MonitorView({
  items,
  selectedId,
  onSelect
}: {
  items: MonitorItem[];
  selectedId?: number;
  onSelect: (id: number) => void;
}) {
  return (
    <section className="panel">
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>饰品</th>
              <th>状态</th>
              <th>底价</th>
              <th>在售</th>
              <th>最高求购</th>
              <th>求购</th>
              <th>24h 成交</th>
              <th>买入分</th>
              <th>卖出分</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr className={item.id === selectedId ? "selected" : ""} key={item.id} onClick={() => onSelect(item.id)}>
                <td>
                  <strong>{item.display_name}</strong>
                  <span>{item.market_hash_name}</span>
                </td>
                <td><span className="tag">{item.status}</span></td>
                <td>¥{item.latest_snapshot?.lowest_price.toFixed(2) ?? "-"}</td>
                <td>{item.latest_snapshot?.sell_count ?? "-"}</td>
                <td>¥{item.latest_snapshot?.highest_buy_price.toFixed(2) ?? "-"}</td>
                <td>{item.latest_snapshot?.buy_count ?? "-"}</td>
                <td>{item.latest_snapshot?.volume_24h ?? "-"}</td>
                <td>{item.buy_score}</td>
                <td>{item.sell_score}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function DetailView({ detail }: { detail: ItemDetail | null }) {
  if (!detail) {
    return <div className="empty">请选择饰品，或先执行一轮采集</div>;
  }
  const latest = detail.snapshots[detail.snapshots.length - 1];
  return (
    <div className="detail-grid">
      <section className="panel summary">
        <div>
          <h2>{detail.display_name}</h2>
          <p>{detail.market_hash_name}</p>
        </div>
        <Metric label="状态" value={detail.status} />
        <Metric label="买入分" value={String(detail.buy_score)} tone="up" />
        <Metric label="卖出分" value={String(detail.sell_score)} tone="down" />
        <Metric label="最新底价" value={`¥${latest?.lowest_price.toFixed(2) ?? "-"}`} />
      </section>
      <section className="panel">
        <h3>价格走势</h3>
        <MiniChart data={detail.snapshots} field="lowest_price" />
      </section>
      <section className="panel">
        <h3>在售数量</h3>
        <MiniChart data={detail.snapshots} field="sell_count" />
      </section>
      <section className="panel">
        <h3>求购数量</h3>
        <MiniChart data={detail.snapshots} field="buy_count" />
      </section>
      <section className="panel">
        <h3>24h 成交</h3>
        <MiniChart data={detail.snapshots} field="volume_24h" kind="bar" />
      </section>
      <section className="panel wide">
        <h3>历史告警</h3>
        <AlertList alerts={detail.alerts} />
      </section>
    </div>
  );
}

function OpportunityView({
  items,
  onSelect,
  setTab
}: {
  items: MonitorItem[];
  onSelect: (id: number) => void;
  setTab: (tab: Tab) => void;
}) {
  const sorted = [...items].sort((a, b) => Math.max(b.buy_score, b.sell_score) - Math.max(a.buy_score, a.sell_score));
  return (
    <div className="opportunity-grid">
      {sorted.map((item) => (
        <button
          className="opportunity"
          key={item.id}
          onClick={() => {
            onSelect(item.id);
            setTab("detail");
          }}
        >
          <strong>{item.display_name}</strong>
          <span>{item.status}</span>
          <div>
            <Metric label="买入" value={String(item.buy_score)} tone="up" />
            <Metric label="卖出" value={String(item.sell_score)} tone="down" />
          </div>
        </button>
      ))}
    </div>
  );
}

function SettingsView() {
  return (
    <section className="panel settings">
      <h2>默认策略</h2>
      <div className="settings-grid">
        <Metric label="在售绝对变化" value="30" />
        <Metric label="在售变化率" value="12%" />
        <Metric label="底价变化率" value="3.5%" />
        <Metric label="求购变化率" value="12%" />
        <Metric label="冷却时间" value="20 分钟" />
        <Metric label="推送渠道" value="微信 / QQ 预留" />
      </div>
    </section>
  );
}

function SourceView({ items, alerts }: { items: MonitorItem[]; alerts: Alert[] }) {
  const hasSnapshots = items.some((item) => item.latest_snapshot);
  return (
    <section className="panel settings">
      <h2>数据源状态</h2>
      <div className="settings-grid">
        <Metric label="API 状态" value="在线" tone="up" />
        <Metric label="行情来源" value="Mock / Steam 适配层" />
        <Metric label="监控饰品" value={`${items.length} 个`} />
        <Metric label="快照状态" value={hasSnapshots ? "已入库" : "待采集"} />
        <Metric label="最近告警" value={`${alerts.length} 条`} />
        <Metric label="worker" value="本地手动采集 / Docker 常驻" />
      </div>
    </section>
  );
}

function title(tab: Tab) {
  const map: Record<Tab, string> = {
    monitor: "监控总览",
    detail: "饰品详情",
    alerts: "异动告警",
    opportunities: "机会榜",
    settings: "策略配置",
    source: "数据源状态"
  };
  return map[tab];
}
