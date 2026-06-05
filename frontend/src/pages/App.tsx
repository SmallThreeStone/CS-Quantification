import { Activity, Bell, Database, Gauge, RefreshCw, Settings, Target } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { api } from "../api/client";
import { AlertList } from "../components/AlertList";
import { Metric } from "../components/Metric";
import { MiniChart } from "../components/MiniChart";
import type { Alert, ItemDetail, MonitorItem, PushRecord, StrategyConfig, StrategyConfigUpdate } from "../types";

type Tab = "monitor" | "detail" | "alerts" | "opportunities" | "settings" | "source";

export default function App() {
  const [tab, setTab] = useState<Tab>("monitor");
  const [items, setItems] = useState<MonitorItem[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [pushRecords, setPushRecords] = useState<PushRecord[]>([]);
  const [strategy, setStrategy] = useState<StrategyConfig | null>(null);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [detail, setDetail] = useState<ItemDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const selected = useMemo(() => items.find((item) => item.id === selectedId) ?? items[0], [items, selectedId]);

  async function refresh() {
    setLoading(true);
    try {
      const [nextItems, nextAlerts, nextPushRecords, nextStrategy] = await Promise.all([
        api.monitor(),
        api.alerts(),
        api.pushRecords(),
        api.strategy()
      ]);
      setItems(nextItems);
      setAlerts(nextAlerts);
      setPushRecords(nextPushRecords);
      setStrategy(nextStrategy);
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
        {tab === "settings" && <SettingsView strategy={strategy} onSaved={setStrategy} />}
        {tab === "source" && <SourceView items={items} alerts={alerts} pushRecords={pushRecords} />}
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

function SettingsView({
  strategy,
  onSaved
}: {
  strategy: StrategyConfig | null;
  onSaved: (strategy: StrategyConfig) => void;
}) {
  const [form, setForm] = useState<StrategyConfigUpdate | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!strategy) {
      return;
    }
    setForm({
      min_absolute_sell_change: strategy.min_absolute_sell_change,
      min_sell_change_rate: strategy.min_sell_change_rate,
      min_price_change_rate: strategy.min_price_change_rate,
      min_buy_change_rate: strategy.min_buy_change_rate,
      cooldown_minutes: strategy.cooldown_minutes
    });
  }, [strategy]);

  async function save() {
    if (!form) {
      return;
    }
    setSaving(true);
    try {
      const saved = await api.updateStrategy(form);
      onSaved(saved);
    } finally {
      setSaving(false);
    }
  }

  if (!form) {
    return <div className="empty">策略配置加载中</div>;
  }

  return (
    <section className="panel settings">
      <h2>默认策略</h2>
      <div className="strategy-form">
        <NumberField
          label="在售绝对变化"
          value={form.min_absolute_sell_change}
          min={1}
          max={10000}
          step={1}
          onChange={(value) => setForm({ ...form, min_absolute_sell_change: value })}
        />
        <NumberField
          label="在售变化率 %"
          value={toPercent(form.min_sell_change_rate)}
          min={1}
          max={500}
          step={1}
          onChange={(value) => setForm({ ...form, min_sell_change_rate: fromPercent(value) })}
        />
        <NumberField
          label="底价变化率 %"
          value={toPercent(form.min_price_change_rate)}
          min={0.1}
          max={100}
          step={0.1}
          onChange={(value) => setForm({ ...form, min_price_change_rate: fromPercent(value) })}
        />
        <NumberField
          label="求购变化率 %"
          value={toPercent(form.min_buy_change_rate)}
          min={1}
          max={500}
          step={1}
          onChange={(value) => setForm({ ...form, min_buy_change_rate: fromPercent(value) })}
        />
        <NumberField
          label="冷却时间 分钟"
          value={form.cooldown_minutes}
          min={0}
          max={1440}
          step={1}
          onChange={(value) => setForm({ ...form, cooldown_minutes: value })}
        />
      </div>
      <div className="settings-actions">
        <Metric label="当前版本" value={strategy?.name ?? "default"} />
        <button className="primary" onClick={save} disabled={saving}>
          <Settings size={16} /> 保存策略
        </button>
      </div>
    </section>
  );
}

function NumberField({
  label,
  value,
  min,
  max,
  step,
  onChange
}: {
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  onChange: (value: number) => void;
}) {
  return (
    <label className="field">
      <span>{label}</span>
      <input
        type="number"
        value={Number.isInteger(value) ? value : Number(value.toFixed(2))}
        min={min}
        max={max}
        step={step}
        onChange={(event) => onChange(Number(event.target.value))}
      />
    </label>
  );
}

function toPercent(value: number) {
  return value * 100;
}

function fromPercent(value: number) {
  return Number((value / 100).toFixed(4));
}

function SourceView({
  items,
  alerts,
  pushRecords
}: {
  items: MonitorItem[];
  alerts: Alert[];
  pushRecords: PushRecord[];
}) {
  const hasSnapshots = items.some((item) => item.latest_snapshot);
  const latestPush = pushRecords[0];
  return (
    <section className="panel settings">
      <h2>数据源状态</h2>
      <div className="settings-grid">
        <Metric label="API 状态" value="在线" tone="up" />
        <Metric label="行情来源" value="Mock / Steam 适配层" />
        <Metric label="监控饰品" value={`${items.length} 个`} />
        <Metric label="快照状态" value={hasSnapshots ? "已入库" : "待采集"} />
        <Metric label="最近告警" value={`${alerts.length} 条`} />
        <Metric label="最近推送" value={latestPush ? `${latestPush.channel}:${latestPush.status}` : "暂无"} />
        <Metric label="worker" value="本地手动采集 / Docker 常驻" />
      </div>
      <div className="push-table">
        <h3>推送记录</h3>
        {pushRecords.length ? (
          pushRecords.slice(0, 8).map((record) => (
            <div className="push-row" key={record.id}>
              <span>{new Date(record.created_at).toLocaleString()}</span>
              <strong>{record.channel}</strong>
              <span>{record.status}</span>
              <span>{record.error || "ok"}</span>
            </div>
          ))
        ) : (
          <div className="empty">暂无推送记录</div>
        )}
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
