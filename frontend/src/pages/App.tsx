import { Activity, BarChart3, Bell, Database, Gauge, PackagePlus, RefreshCw, Settings, Target } from "lucide-react";
import type { CSSProperties } from "react";
import { useEffect, useMemo, useState } from "react";

import { api } from "../api/client";
import { AlertList } from "../components/AlertList";
import { Metric } from "../components/Metric";
import { MiniChart } from "../components/MiniChart";
import type {
  Alert,
  BacktestResult,
  BacktestSummary,
  CollectRun,
  ItemDetail,
  ManagedItem,
  ManagedItemInput,
  MonitorPool,
  MonitorItem,
  PushRecord,
  StrategyConfig,
  StrategyConfigUpdate
} from "../types";

type Tab = "monitor" | "detail" | "alerts" | "opportunities" | "items" | "backtests" | "settings" | "source";

export default function App() {
  const [tab, setTab] = useState<Tab>("monitor");
  const [items, setItems] = useState<MonitorItem[]>([]);
  const [managedItems, setManagedItems] = useState<ManagedItem[]>([]);
  const [pools, setPools] = useState<MonitorPool[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [pushRecords, setPushRecords] = useState<PushRecord[]>([]);
  const [backtests, setBacktests] = useState<BacktestResult[]>([]);
  const [backtestSummary, setBacktestSummary] = useState<BacktestSummary[]>([]);
  const [collectRuns, setCollectRuns] = useState<CollectRun[]>([]);
  const [strategy, setStrategy] = useState<StrategyConfig | null>(null);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [detail, setDetail] = useState<ItemDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const selected = useMemo(() => items.find((item) => item.id === selectedId) ?? items[0], [items, selectedId]);

  async function refresh() {
    setLoading(true);
    try {
      const [
        nextItems,
        nextManagedItems,
        nextPools,
        nextAlerts,
        nextPushRecords,
        nextBacktests,
        nextBacktestSummary,
        nextCollectRuns,
        nextStrategy
      ] = await Promise.all([
        api.monitor(),
        api.items(),
        api.monitorPools(),
        api.alerts(),
        api.pushRecords(),
        api.backtests(),
        api.backtestSummary(),
        api.collectRuns(),
        api.strategy()
      ]);
      setItems(nextItems);
      setManagedItems(nextManagedItems);
      setPools(nextPools);
      setAlerts(nextAlerts);
      setPushRecords(nextPushRecords);
      setBacktests(nextBacktests);
      setBacktestSummary(nextBacktestSummary);
      setCollectRuns(nextCollectRuns);
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

  async function evaluateBacktests() {
    setLoading(true);
    try {
      await api.evaluateBacktests();
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
          <button className={tab === "items" ? "active" : ""} onClick={() => setTab("items")}>
            <PackagePlus size={18} /> 饰品管理
          </button>
          <button className={tab === "backtests" ? "active" : ""} onClick={() => setTab("backtests")}>
            <BarChart3 size={18} /> 告警回测
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
        {tab === "items" && <ItemManager items={managedItems} pools={pools} onChanged={refresh} />}
        {tab === "backtests" && (
          <BacktestView summary={backtestSummary} results={backtests} onEvaluate={evaluateBacktests} loading={loading} />
        )}
        {tab === "settings" && <SettingsView strategy={strategy} onSaved={setStrategy} />}
        {tab === "source" && (
          <SourceView items={items} pools={pools} alerts={alerts} pushRecords={pushRecords} collectRuns={collectRuns} />
        )}
      </main>
    </div>
  );
}

function BacktestView({
  summary,
  results,
  onEvaluate,
  loading
}: {
  summary: BacktestSummary[];
  results: BacktestResult[];
  onEvaluate: () => Promise<void>;
  loading: boolean;
}) {
  return (
    <div className="detail-grid">
      <section className="panel wide">
        <div className="section-head">
          <h2>回测汇总</h2>
          <button className="primary compact-button" onClick={onEvaluate} disabled={loading}>
            <BarChart3 size={16} /> 刷新回测
          </button>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>类型</th>
                <th>窗口</th>
                <th>样本</th>
                <th>命中</th>
                <th>胜率</th>
                <th>平均变化</th>
              </tr>
            </thead>
            <tbody>
              {summary.map((row) => (
                <tr key={`${row.alert_type}-${row.horizon_minutes}`}>
                  <td>{row.alert_type}</td>
                  <td>{formatHorizon(row.horizon_minutes)}</td>
                  <td>{row.sample_count}</td>
                  <td>{row.win_count}</td>
                  <td>{formatPercent(row.win_rate)}</td>
                  <td className={row.avg_change_rate >= 0 ? "up" : "down"}>{formatPercent(row.avg_change_rate)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {!summary.length && <div className="empty">暂无可评估回测</div>}
      </section>
      <section className="panel wide">
        <h2>最近结果</h2>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>饰品</th>
                <th>类型</th>
                <th>判断</th>
                <th>窗口</th>
                <th>入场</th>
                <th>评估</th>
                <th>变化</th>
              </tr>
            </thead>
            <tbody>
              {results.map((row) => (
                <tr key={row.id}>
                  <td>{row.item_name}</td>
                  <td>{row.alert_type}</td>
                  <td>{row.direction}</td>
                  <td>{formatHorizon(row.horizon_minutes)}</td>
                  <td>¥{row.entry_price.toFixed(2)}</td>
                  <td>¥{row.exit_price.toFixed(2)}</td>
                  <td className={row.change_rate >= 0 ? "up" : "down"}>{formatPercent(row.change_rate)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {!results.length && <div className="empty">暂无回测结果</div>}
      </section>
    </div>
  );
}

const emptyItem: ManagedItemInput = {
  market_hash_name: "",
  display_name: "",
  exterior: "",
  category: "",
  is_active: true,
  pool_id: null
};

function ItemManager({
  items,
  pools,
  onChanged
}: {
  items: ManagedItem[];
  pools: MonitorPool[];
  onChanged: () => Promise<void>;
}) {
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState<ManagedItemInput>(emptyItem);
  const [saving, setSaving] = useState(false);

  function edit(item: ManagedItem) {
    setEditingId(item.id);
    setForm({
      market_hash_name: item.market_hash_name,
      display_name: item.display_name,
      exterior: item.exterior,
      category: item.category,
      is_active: item.is_active,
      pool_id: item.pool_id
    });
  }

  async function save() {
    setSaving(true);
    try {
      if (editingId) {
        await api.updateItem(editingId, form);
      } else {
        await api.createItem(form);
      }
      setEditingId(null);
      setForm(emptyItem);
      await onChanged();
    } finally {
      setSaving(false);
    }
  }

  async function toggle(item: ManagedItem) {
    await api.setItemActive(item.id, !item.is_active);
    await onChanged();
  }

  return (
    <section className="panel item-manager">
      <div className="item-form">
        <label className="field wide-field">
          <span>Market Hash Name</span>
          <input
            value={form.market_hash_name}
            onChange={(event) => setForm({ ...form, market_hash_name: event.target.value })}
          />
        </label>
        <label className="field">
          <span>显示名</span>
          <input value={form.display_name} onChange={(event) => setForm({ ...form, display_name: event.target.value })} />
        </label>
        <label className="field">
          <span>品质</span>
          <input value={form.exterior} onChange={(event) => setForm({ ...form, exterior: event.target.value })} />
        </label>
        <label className="field">
          <span>分类</span>
          <input value={form.category} onChange={(event) => setForm({ ...form, category: event.target.value })} />
        </label>
        <label className="field">
          <span>监控池</span>
          <select
            value={form.pool_id ?? ""}
            onChange={(event) => setForm({ ...form, pool_id: event.target.value ? Number(event.target.value) : null })}
          >
            <option value="">未分组</option>
            {pools.map((pool) => (
              <option key={pool.id} value={pool.id}>
                {pool.name}
              </option>
            ))}
          </select>
        </label>
        <label className="check-field">
          <input
            type="checkbox"
            checked={form.is_active}
            onChange={(event) => setForm({ ...form, is_active: event.target.checked })}
          />
          <span>加入监控</span>
        </label>
        <button className="primary save-item" onClick={save} disabled={saving || !form.market_hash_name || !form.display_name}>
          <PackagePlus size={16} /> {editingId ? "保存饰品" : "新增饰品"}
        </button>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>饰品</th>
              <th>品质</th>
              <th>分类</th>
              <th>监控池</th>
              <th>状态</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.id}>
                <td>
                  <strong>{item.display_name}</strong>
                  <span>{item.market_hash_name}</span>
                </td>
                <td>{item.exterior || "-"}</td>
                <td>{item.category || "-"}</td>
                <td>{item.pool_name || "未分组"}</td>
                <td><span className="tag">{item.is_active ? "监控中" : "已停用"}</span></td>
                <td>
                  <div className="row-actions">
                    <button onClick={() => edit(item)}>编辑</button>
                    <button onClick={() => toggle(item)}>{item.is_active ? "停用" : "恢复"}</button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
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
              <th>池</th>
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
                <td>{item.pool_name ?? "未分组"}</td>
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
        <h3>时间段热力图</h3>
        <HeatmapView detail={detail} />
      </section>
      <section className="panel wide">
        <h3>历史告警简报</h3>
        <AlertSummaryView detail={detail} />
      </section>
      <section className="panel wide">
        <h3>历史告警</h3>
        <AlertList alerts={detail.alerts} />
      </section>
    </div>
  );
}

function HeatmapView({ detail }: { detail: ItemDetail }) {
  const maxActivity = Math.max(
    ...detail.heatmap.map((row) => row.max_sell_change + row.max_buy_change + row.avg_volume_24h),
    1
  );
  if (!detail.heatmap.length) {
    return <div className="empty-chart">暂无热力数据</div>;
  }
  return (
    <div className="heatmap-grid">
      {detail.heatmap.map((row) => {
        const intensity = Math.min(1, (row.max_sell_change + row.max_buy_change + row.avg_volume_24h) / maxActivity);
        return (
          <div className="heat-cell" style={{ "--heat": intensity } as CSSProperties} key={row.hour}>
            <strong>{String(row.hour).padStart(2, "0")}:00</strong>
            <span>在售 {row.avg_sell_count.toFixed(0)}</span>
            <span>求购 {row.avg_buy_count.toFixed(0)}</span>
            <span>波动 {Math.max(row.max_sell_change, row.max_buy_change).toFixed(0)}</span>
          </div>
        );
      })}
    </div>
  );
}

function AlertSummaryView({ detail }: { detail: ItemDetail }) {
  if (!detail.alert_summary.length) {
    return <div className="empty-chart">暂无告警简报</div>;
  }
  return (
    <div className="summary-list">
      {detail.alert_summary.map((group) => (
        <div className="summary-row" key={group.alert_type}>
          <div>
            <strong>{group.alert_type}</strong>
            <span>{group.total_count} 次</span>
          </div>
          <div className="summary-alerts">
            {group.recent_alerts.map((alert) => (
              <span className={alert.absolute_change >= 0 ? "up" : "down"} key={alert.id}>
                {formatTime(alert.created_at)} {alert.previous_value.toFixed(0)}→{alert.current_value.toFixed(0)} (
                {alert.absolute_change >= 0 ? "+" : ""}
                {alert.absolute_change.toFixed(0)})
              </span>
            ))}
          </div>
        </div>
      ))}
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
  pools,
  alerts,
  pushRecords,
  collectRuns
}: {
  items: MonitorItem[];
  pools: MonitorPool[];
  alerts: Alert[];
  pushRecords: PushRecord[];
  collectRuns: CollectRun[];
}) {
  const hasSnapshots = items.some((item) => item.latest_snapshot);
  const latestPush = pushRecords[0];
  const latestRun = collectRuns[0];
  const qualityTotal = latestRun ? latestRun.real_field_count + latestRun.fallback_field_count : 0;
  const qualityRatio = qualityTotal ? latestRun!.real_field_count / qualityTotal : 0;
  return (
    <section className="panel settings">
      <h2>数据源状态</h2>
      <div className="settings-grid">
        <Metric label="API 状态" value="在线" tone="up" />
        <Metric label="行情来源" value="Mock / Steam 适配层" />
        <Metric label="监控饰品" value={`${items.length} 个`} />
        <Metric label="监控池" value={`${pools.length} 个`} />
        <Metric label="快照状态" value={hasSnapshots ? "已入库" : "待采集"} />
        <Metric label="最近告警" value={`${alerts.length} 条`} />
        <Metric label="最近采集" value={latestRun ? `${latestRun.status}:${latestRun.snapshot_count}` : "暂无"} />
        <Metric label="真实字段占比" value={latestRun ? formatPercent(qualityRatio) : "暂无"} tone={qualityRatio > 0.5 ? "up" : "neutral"} />
        <Metric label="补位次数" value={latestRun ? `${latestRun.fallback_count} 次` : "暂无"} />
        <Metric label="最近推送" value={latestPush ? `${latestPush.channel}:${latestPush.status}` : "暂无"} />
        <Metric label="worker" value="本地手动采集 / Docker 常驻" />
      </div>
      <div className="push-table">
        <h3>采集记录</h3>
        {collectRuns.length ? (
          collectRuns.slice(0, 8).map((run) => (
            <div className="collect-row" key={run.id}>
              <span>{new Date(run.started_at).toLocaleString()}</span>
              <strong>{run.mode}</strong>
              <span>{run.status}</span>
              <span>{run.provider}</span>
              <span>{run.snapshot_count}/{run.item_count}</span>
              <span>真 {run.real_field_count}</span>
              <span>补 {run.fallback_field_count}</span>
              <span>回退 {run.fallback_count}</span>
              <span>{run.alert_count} 告警</span>
              <span>{run.duration_ms}ms</span>
              {run.error ? <span className="collect-error">{run.error}</span> : <span className="collect-error">ok</span>}
            </div>
          ))
        ) : (
          <div className="empty">暂无采集记录</div>
        )}
      </div>
      <div className="push-table">
        <h3>监控池</h3>
        {pools.map((pool) => (
          <div className="push-row" key={pool.id}>
            <span>{pool.name}</span>
            <strong>{pool.interval_minutes} 分钟</strong>
            <span>{pool.active_item_count} 个饰品</span>
            <span>{pool.last_collected_at ? new Date(pool.last_collected_at).toLocaleString() : "待采集"}</span>
          </div>
        ))}
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
    items: "饰品管理",
    backtests: "告警回测",
    settings: "策略配置",
    source: "数据源状态"
  };
  return map[tab];
}

function formatHorizon(minutes: number) {
  if (minutes < 60) {
    return `${minutes} 分钟`;
  }
  if (minutes < 1440) {
    return `${minutes / 60} 小时`;
  }
  return `${minutes / 1440} 天`;
}

function formatPercent(value: number) {
  return `${(value * 100).toFixed(2)}%`;
}

function formatTime(value: string) {
  const date = new Date(value);
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  const hour = String(date.getHours()).padStart(2, "0");
  const minute = String(date.getMinutes()).padStart(2, "0");
  return `${month}-${day} ${hour}:${minute}`;
}
