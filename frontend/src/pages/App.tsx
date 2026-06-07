import { Activity, BarChart3, Bell, Database, Gauge, PackagePlus, RefreshCw, Settings, Target } from "lucide-react";
import type { CSSProperties } from "react";
import { useEffect, useMemo, useState } from "react";

import { api } from "../api/client";
import type { AlertFilters } from "../api/client";
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
  MonitorPoolInput,
  MonitorItem,
  OpsHealth,
  OpsReadiness,
  P0Summary,
  PushRecord,
  Retention,
  SourceConfig,
  SourceFieldQuality,
  StrategyConfig,
  StrategyConfigUpdate,
  TuningSuggestion
} from "../types";

type Tab = "monitor" | "detail" | "alerts" | "opportunities" | "items" | "backtests" | "settings" | "source";
type MonitorSortKey = "activity" | "price" | "sell" | "buy" | "spread" | "volume" | "buyScore" | "sellScore";
type SortDirection = "asc" | "desc";

export default function App() {
  const [tab, setTab] = useState<Tab>("monitor");
  const [items, setItems] = useState<MonitorItem[]>([]);
  const [managedItems, setManagedItems] = useState<ManagedItem[]>([]);
  const [pools, setPools] = useState<MonitorPool[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [alertFilters, setAlertFilters] = useState<AlertFilters>({});
  const [pushRecords, setPushRecords] = useState<PushRecord[]>([]);
  const [opsHealth, setOpsHealth] = useState<OpsHealth | null>(null);
  const [opsReadiness, setOpsReadiness] = useState<OpsReadiness | null>(null);
  const [p0Summary, setP0Summary] = useState<P0Summary | null>(null);
  const [sourceConfig, setSourceConfig] = useState<SourceConfig | null>(null);
  const [sourceFieldQuality, setSourceFieldQuality] = useState<SourceFieldQuality | null>(null);
  const [retention, setRetention] = useState<Retention | null>(null);
  const [backtests, setBacktests] = useState<BacktestResult[]>([]);
  const [backtestSummary, setBacktestSummary] = useState<BacktestSummary[]>([]);
  const [tuningSuggestions, setTuningSuggestions] = useState<TuningSuggestion[]>([]);
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
        nextOpsHealth,
        nextOpsReadiness,
        nextP0Summary,
        nextSourceConfig,
        nextSourceFieldQuality,
        nextRetention,
        nextBacktests,
        nextBacktestSummary,
        nextTuningSuggestions,
        nextCollectRuns,
        nextStrategy
      ] = await Promise.all([
        api.monitor(),
        api.items(),
        api.monitorPools(),
        api.alerts(alertFilters),
        api.pushRecords(),
        api.opsHealth(),
        api.opsReadiness(),
        api.p0Summary(),
        api.sourceConfig(),
        api.sourceFieldQuality(),
        api.retention(),
        api.backtests(),
        api.backtestSummary(),
        api.tuningSuggestions(),
        api.collectRuns(),
        api.strategy()
      ]);
      setItems(nextItems);
      setManagedItems(nextManagedItems);
      setPools(nextPools);
      setAlerts(nextAlerts);
      setPushRecords(nextPushRecords);
      setOpsHealth(nextOpsHealth);
      setOpsReadiness(nextOpsReadiness);
      setP0Summary(nextP0Summary);
      setSourceConfig(nextSourceConfig);
      setSourceFieldQuality(nextSourceFieldQuality);
      setRetention(nextRetention);
      setBacktests(nextBacktests);
      setBacktestSummary(nextBacktestSummary);
      setTuningSuggestions(nextTuningSuggestions);
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
  }, [alertFilters]);

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
        {tab === "alerts" && (
          <AlertCenter
            alerts={alerts}
            filters={alertFilters}
            onFiltersChange={setAlertFilters}
            managedItems={managedItems}
          />
        )}
        {tab === "opportunities" && <OpportunityView items={items} onSelect={setSelectedId} setTab={setTab} />}
        {tab === "items" && <ItemManager items={managedItems} pools={pools} onChanged={refresh} />}
        {tab === "backtests" && (
          <BacktestView
            summary={backtestSummary}
            suggestions={tuningSuggestions}
            results={backtests}
            onEvaluate={evaluateBacktests}
            loading={loading}
          />
        )}
        {tab === "settings" && <SettingsView strategy={strategy} onSaved={setStrategy} />}
        {tab === "source" && (
          <SourceView
            items={items}
            pools={pools}
            alerts={alerts}
            pushRecords={pushRecords}
            collectRuns={collectRuns}
            opsHealth={opsHealth}
            opsReadiness={opsReadiness}
            p0Summary={p0Summary}
            sourceConfig={sourceConfig}
            sourceFieldQuality={sourceFieldQuality}
            retention={retention}
          />
        )}
      </main>
    </div>
  );
}

function BacktestView({
  summary,
  suggestions,
  results,
  onEvaluate,
  loading
}: {
  summary: BacktestSummary[];
  suggestions: TuningSuggestion[];
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
                <th>最大上涨</th>
                <th>最大回撤</th>
                <th>盈亏比</th>
                <th>置信</th>
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
                  <td className="up">{formatPercent(row.max_gain_rate)}</td>
                  <td className="down">{formatPercent(row.max_drawdown_rate)}</td>
                  <td>{row.profit_loss_ratio ? row.profit_loss_ratio.toFixed(2) : "-"}</td>
                  <td>
                    <span className={`quality-tag ${confidenceClass(row.confidence_level)}`}>{row.confidence_level}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {!summary.length && <div className="empty">暂无可评估回测</div>}
      </section>
      <section className="panel wide">
        <h2>调参建议</h2>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>类型</th>
                <th>窗口</th>
                <th>样本</th>
                <th>建议</th>
                <th>参数</th>
                <th>依据</th>
              </tr>
            </thead>
            <tbody>
              {suggestions.map((row) => (
                <tr key={`${row.alert_type}-${row.horizon_minutes}`}>
                  <td>{row.alert_type}</td>
                  <td>{formatHorizon(row.horizon_minutes)}</td>
                  <td>{row.sample_count}</td>
                  <td><span className={`quality-tag ${suggestionClass(row.action)}`}>{row.action}</span></td>
                  <td>{row.parameter_hint}</td>
                  <td>{row.reason}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {!suggestions.length && <div className="empty">暂无调参建议</div>}
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
                <th>评估时间</th>
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
                  <td>{formatDate(row.evaluated_at)}</td>
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

function AlertCenter({
  alerts,
  filters,
  onFiltersChange,
  managedItems
}: {
  alerts: Alert[];
  filters: AlertFilters;
  onFiltersChange: (filters: AlertFilters) => void;
  managedItems: ManagedItem[];
}) {
  const itemOptions = useMemo(
    () => Array.from(new Set(managedItems.map((item) => item.display_name))).filter(Boolean).sort(),
    [managedItems]
  );
  const alertTypes = ["在售变化", "求购变化", "底价变化", "价格波动异常", "成交量异常"];
  const severities = ["P1", "P2", "P3"];
  const platforms = Array.from(new Set(alerts.map((alert) => alert.platform_name))).filter(Boolean).sort();

  function update(key: keyof AlertFilters, value: string) {
    onFiltersChange({ ...filters, [key]: value || undefined });
  }

  return (
    <section className="panel">
      <div className="filter-bar">
        <label className="field compact-field">
          <span>饰品</span>
          <input
            list="alert-item-options"
            value={filters.item ?? ""}
            onChange={(event) => update("item", event.target.value)}
            placeholder="全部"
          />
          <datalist id="alert-item-options">
            {itemOptions.map((name) => (
              <option key={name} value={name} />
            ))}
          </datalist>
        </label>
        <SelectFilter label="类型" value={filters.alert_type ?? ""} options={alertTypes} onChange={(value) => update("alert_type", value)} />
        <SelectFilter label="严重度" value={filters.severity ?? ""} options={severities} onChange={(value) => update("severity", value)} />
        <SelectFilter label="平台" value={filters.platform ?? ""} options={platforms} onChange={(value) => update("platform", value)} />
        <button className="ghost-button" onClick={() => onFiltersChange({})}>
          清空筛选
        </button>
      </div>
      <AlertList alerts={alerts} />
    </section>
  );
}

function SelectFilter({
  label,
  value,
  options,
  onChange
}: {
  label: string;
  value: string;
  options: string[];
  onChange: (value: string) => void;
}) {
  return (
    <label className="field compact-field">
      <span>{label}</span>
      <select value={value} onChange={(event) => onChange(event.target.value)}>
        <option value="">全部</option>
        {options.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
    </label>
  );
}

const emptyItem: ManagedItemInput = {
  market_hash_name: "",
  display_name: "",
  exterior: "",
  category: "",
  steam_item_nameid: "",
  is_active: true,
  pool_id: null
};

const emptyPool: MonitorPoolInput = {
  name: "",
  interval_minutes: 10,
  description: ""
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
  const [editingPoolId, setEditingPoolId] = useState<number | null>(null);
  const [poolForm, setPoolForm] = useState<MonitorPoolInput>(emptyPool);
  const [saving, setSaving] = useState(false);
  const [savingPool, setSavingPool] = useState(false);
  const [discoveringId, setDiscoveringId] = useState<number | null>(null);
  const [validatingId, setValidatingId] = useState<number | null>(null);
  const [batching, setBatching] = useState<"discover" | "validate" | null>(null);
  const [validationMessage, setValidationMessage] = useState("");

  function edit(item: ManagedItem) {
    setEditingId(item.id);
    setForm({
      market_hash_name: item.market_hash_name,
      display_name: item.display_name,
      exterior: item.exterior,
      category: item.category,
      steam_item_nameid: item.steam_item_nameid,
      is_active: item.is_active,
      pool_id: item.pool_id
    });
  }

  function editPool(pool: MonitorPool) {
    setEditingPoolId(pool.id);
    setPoolForm({
      name: pool.name,
      interval_minutes: pool.interval_minutes,
      description: pool.description
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

  async function savePool() {
    setSavingPool(true);
    try {
      if (editingPoolId) {
        await api.updateMonitorPool(editingPoolId, poolForm);
      } else {
        await api.createMonitorPool(poolForm);
      }
      setEditingPoolId(null);
      setPoolForm(emptyPool);
      await onChanged();
    } finally {
      setSavingPool(false);
    }
  }

  async function toggle(item: ManagedItem) {
    await api.setItemActive(item.id, !item.is_active);
    await onChanged();
  }

  async function discover(item: ManagedItem) {
    setDiscoveringId(item.id);
    try {
      await api.discoverSteamNameId(item.id);
      await onChanged();
    } catch (error) {
      alert(error instanceof Error ? error.message : "Steam NameID 发现失败");
    } finally {
      setDiscoveringId(null);
    }
  }

  async function validate(item: ManagedItem) {
    setValidatingId(item.id);
    setValidationMessage("");
    try {
      const result = await api.validateSteamNameId(item.id);
      setValidationMessage(
        result.ok
          ? `${item.display_name} 订单簿可用：在售 ${result.sell_count}，求购 ${result.buy_count}，最高求购 ¥${result.highest_buy_price.toFixed(2)}`
          : `${item.display_name} 订单簿不可用：${result.error}`
      );
    } finally {
      setValidatingId(null);
    }
  }

  async function batchDiscover() {
    setBatching("discover");
    setValidationMessage("");
    try {
      const result = await api.discoverMissingSteamNameIds();
      setValidationMessage(batchMessage("批量发现", result));
      await onChanged();
    } finally {
      setBatching(null);
    }
  }

  async function batchValidate() {
    setBatching("validate");
    setValidationMessage("");
    try {
      const result = await api.validateAllSteamNameIds();
      setValidationMessage(batchMessage("批量验证", result));
    } finally {
      setBatching(null);
    }
  }

  return (
    <div className="item-manager-layout">
      <section className="panel item-manager">
        <div className="section-head">
          <h2>监控池管理</h2>
          <span className="tag">{pools.length} 个池</span>
        </div>
        <div className="pool-form">
          <label className="field">
            <span>池名称</span>
            <input value={poolForm.name} onChange={(event) => setPoolForm({ ...poolForm, name: event.target.value })} />
          </label>
          <label className="field">
            <span>采集间隔 分钟</span>
            <input
              type="number"
              min={1}
              max={1440}
              value={poolForm.interval_minutes}
              onChange={(event) => setPoolForm({ ...poolForm, interval_minutes: Number(event.target.value) })}
            />
          </label>
          <label className="field pool-description">
            <span>说明</span>
            <input
              value={poolForm.description}
              onChange={(event) => setPoolForm({ ...poolForm, description: event.target.value })}
            />
          </label>
          <button className="primary save-item" onClick={savePool} disabled={savingPool || !poolForm.name}>
            <Settings size={16} /> {editingPoolId ? "保存池" : "新增池"}
          </button>
        </div>
        <div className="pool-grid">
          {pools.map((pool) => (
            <button className="pool-card" key={pool.id} onClick={() => editPool(pool)}>
              <div>
                <strong>{pool.name}</strong>
                <span>{pool.description || "暂无说明"}</span>
              </div>
              <Metric label="间隔" value={`${pool.interval_minutes} 分钟`} />
              <Metric label="活跃饰品" value={`${pool.active_item_count} 个`} />
              <Metric
                label="最近采集"
                value={pool.last_collected_at ? formatTime(pool.last_collected_at) : "待采集"}
              />
            </button>
          ))}
        </div>
      </section>

      <section className="panel item-manager">
        <div className="section-head">
          <h2>饰品管理</h2>
          <span className="tag">{items.length} 个饰品</span>
        </div>
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
          <span>Steam NameID</span>
          <input
            value={form.steam_item_nameid}
            onChange={(event) => setForm({ ...form, steam_item_nameid: event.target.value })}
          />
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
        <div className="batch-actions">
          <button onClick={batchDiscover} disabled={batching !== null}>
            {batching === "discover" ? "批量发现中" : "批量发现缺失ID"}
          </button>
          <button onClick={batchValidate} disabled={batching !== null}>
            {batching === "validate" ? "批量验证中" : "批量验深度"}
          </button>
        </div>
        {validationMessage && <div className="inline-status">{validationMessage}</div>}
        <table>
          <thead>
            <tr>
              <th>饰品</th>
              <th>品质</th>
              <th>分类</th>
              <th>NameID</th>
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
                <td>{item.steam_item_nameid || "-"}</td>
                <td>{item.pool_name || "未分组"}</td>
                <td><span className="tag">{item.is_active ? "监控中" : "已停用"}</span></td>
                <td>
                  <div className="row-actions">
                    <button onClick={() => edit(item)}>编辑</button>
                    <button onClick={() => discover(item)} disabled={discoveringId === item.id}>
                      {discoveringId === item.id ? "发现中" : "发现ID"}
                    </button>
                    <button onClick={() => validate(item)} disabled={validatingId === item.id}>
                      {validatingId === item.id ? "验证中" : "验深度"}
                    </button>
                    <button onClick={() => toggle(item)}>{item.is_active ? "停用" : "恢复"}</button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      </section>
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
  const [sortKey, setSortKey] = useState<MonitorSortKey>("activity");
  const [sortDirection, setSortDirection] = useState<SortDirection>("desc");
  const sorted = useMemo(() => {
    return [...items].sort((left, right) => {
      const delta = sortValue(left, sortKey) - sortValue(right, sortKey);
      if (delta === 0) {
        return left.display_name.localeCompare(right.display_name);
      }
      return sortDirection === "asc" ? delta : -delta;
    });
  }, [items, sortDirection, sortKey]);

  function changeSort(nextKey: MonitorSortKey) {
    if (nextKey === sortKey) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
      return;
    }
    setSortKey(nextKey);
    setSortDirection("desc");
  }

  return (
    <section className="panel">
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>饰品</th>
              <SortableHead label="状态" active={sortKey === "activity"} direction={sortDirection} onClick={() => changeSort("activity")} />
              <th>信号</th>
              <th>品类策略</th>
              <th>可信度</th>
              <SortableHead label="底价" active={sortKey === "price"} direction={sortDirection} onClick={() => changeSort("price")} />
              <SortableHead label="在售" active={sortKey === "sell"} direction={sortDirection} onClick={() => changeSort("sell")} />
              <th>最高求购</th>
              <SortableHead label="求购" active={sortKey === "buy"} direction={sortDirection} onClick={() => changeSort("buy")} />
              <SortableHead label="价差率" active={sortKey === "spread"} direction={sortDirection} onClick={() => changeSort("spread")} />
              <SortableHead label="24h 成交" active={sortKey === "volume"} direction={sortDirection} onClick={() => changeSort("volume")} />
              <th>池</th>
              <SortableHead label="买入分" active={sortKey === "buyScore"} direction={sortDirection} onClick={() => changeSort("buyScore")} />
              <SortableHead label="卖出分" active={sortKey === "sellScore"} direction={sortDirection} onClick={() => changeSort("sellScore")} />
            </tr>
          </thead>
          <tbody>
            {sorted.map((item) => (
              <tr className={item.id === selectedId ? "selected" : ""} key={item.id} onClick={() => onSelect(item.id)}>
                <td>
                  <strong>{item.display_name}</strong>
                  <span>{item.market_hash_name}</span>
                </td>
                <td><span className="tag">{item.status}</span></td>
                <td>
                  <span className={`signal-tag ${signalClass(item.decision_signal.action)}`}>
                    {item.decision_signal.action}
                  </span>
                  <span>{item.decision_signal.confidence}</span>
                </td>
                <td>
                  <span className="tag">{item.category_strategy.profile}</span>
                  <span>{strategyAdjustmentText(item.category_strategy.buy_adjustment, item.category_strategy.sell_adjustment)}</span>
                </td>
                <td><span className={`quality-tag ${item.source_quality?.level ?? "unknown"}`}>{qualityText(item)}</span></td>
                <td>¥{item.latest_snapshot?.lowest_price.toFixed(2) ?? "-"}</td>
                <td>{item.latest_snapshot?.sell_count ?? "-"}</td>
                <td>¥{item.latest_snapshot?.highest_buy_price.toFixed(2) ?? "-"}</td>
                <td>{item.latest_snapshot?.buy_count ?? "-"}</td>
                <td>
                  <strong>{item.latest_snapshot ? formatPercent(item.latest_snapshot.spread_rate) : "-"}</strong>
                  {item.latest_snapshot && <span>净 {formatPercent(item.latest_snapshot.net_spread_rate)}</span>}
                </td>
                <td>{item.latest_snapshot?.volume_24h ?? "-"}</td>
                <td>{item.pool_name ?? "未分组"}</td>
                <td>
                  <strong>{item.adjusted_buy_score}</strong>
                  {item.quality_penalty > 0 && <span>原 {item.buy_score}</span>}
                </td>
                <td>
                  <strong>{item.adjusted_sell_score}</strong>
                  {item.quality_penalty > 0 && <span>原 {item.sell_score}</span>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function SortableHead({
  label,
  active,
  direction,
  onClick
}: {
  label: string;
  active: boolean;
  direction: SortDirection;
  onClick: () => void;
}) {
  return (
    <th>
      <button className={`sort-head ${active ? "active" : ""}`} onClick={onClick}>
        {label}
        <span>{active ? (direction === "asc" ? "↑" : "↓") : "↕"}</span>
      </button>
    </th>
  );
}

function sortValue(item: MonitorItem, key: MonitorSortKey) {
  if (key === "activity") {
    return Math.max(item.adjusted_buy_score, item.adjusted_sell_score);
  }
  if (key === "price") {
    return item.latest_snapshot?.lowest_price ?? -1;
  }
  if (key === "sell") {
    return item.latest_snapshot?.sell_count ?? -1;
  }
  if (key === "buy") {
    return item.latest_snapshot?.buy_count ?? -1;
  }
  if (key === "spread") {
    return item.latest_snapshot?.spread_rate ?? -1;
  }
  if (key === "volume") {
    return item.latest_snapshot?.volume_24h ?? -1;
  }
  if (key === "buyScore") {
    return item.adjusted_buy_score;
  }
  return item.adjusted_sell_score;
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
        <Metric label="参考信号" value={`${detail.decision_signal.action} ${detail.decision_signal.confidence}`} tone={signalTone(detail.decision_signal.action)} />
        <Metric label="信号依据" value={detail.decision_signal.reason} />
        <Metric label="品类策略" value={`${detail.category_strategy.profile} ${strategyAdjustmentText(detail.category_strategy.buy_adjustment, detail.category_strategy.sell_adjustment)}`} />
        <Metric label="买入分" value={scoreLabel(detail.adjusted_buy_score, detail.buy_score)} tone="up" />
        <Metric label="卖出分" value={scoreLabel(detail.adjusted_sell_score, detail.sell_score)} tone="down" />
        <Metric label="最新底价" value={`¥${latest?.lowest_price.toFixed(2) ?? "-"}`} />
        <Metric label="买卖价差" value={latest ? `¥${latest.spread_amount.toFixed(2)} / ${formatPercent(latest.spread_rate)}` : "-"} />
        <Metric label="净价差" value={latest ? `¥${latest.net_spread_amount.toFixed(2)} / ${formatPercent(latest.net_spread_rate)}` : "-"} />
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
        <h3>买卖盘价差</h3>
        <MiniChart data={detail.snapshots} field="spread_rate" />
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
        <h3>历史告警时间线</h3>
        <AlertTimeline alerts={detail.alerts} />
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

function AlertTimeline({ alerts }: { alerts: Alert[] }) {
  if (!alerts.length) {
    return <div className="empty-chart">暂无告警时间线</div>;
  }
  return (
    <div className="timeline">
      {alerts.map((alert) => (
        <div className="timeline-row" key={alert.id}>
          <time>{formatTime(alert.created_at)}</time>
          <div>
            <strong>{alert.alert_type}</strong>
            <span>{alert.direction}</span>
          </div>
          <div className={alert.absolute_change >= 0 ? "up" : "down"}>
            {alert.previous_value.toFixed(0)}→{alert.current_value.toFixed(0)}
          </div>
          <span>{formatChange(alert.absolute_change)} / {formatPercent(alert.change_rate)}</span>
        </div>
      ))}
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
  const groups = opportunityGroups(items);
  return (
    <div className="opportunity-sections">
      {groups.map((group) => (
        <section className="panel opportunity-section" key={group.title}>
          <div className="section-head">
            <h2>{group.title}</h2>
            <span className="tag">{group.items.length} 个</span>
          </div>
          {group.items.length ? (
            <div className="opportunity-grid">
              {group.items.map((item) => (
                <OpportunityCard item={item} key={item.id} onSelect={onSelect} setTab={setTab} />
              ))}
            </div>
          ) : (
            <div className="empty compact-empty">暂无匹配饰品</div>
          )}
        </section>
      ))}
    </div>
  );
}

function OpportunityCard({
  item,
  onSelect,
  setTab
}: {
  item: MonitorItem;
  onSelect: (id: number) => void;
  setTab: (tab: Tab) => void;
}) {
  return (
    <button
      className="opportunity"
      onClick={() => {
        onSelect(item.id);
        setTab("detail");
      }}
    >
      <strong>{item.display_name}</strong>
      <span>
        <span className={`signal-tag ${signalClass(item.decision_signal.action)}`}>{item.decision_signal.action}</span>
        {item.status}
      </span>
      <span>{item.category_strategy.profile}</span>
      <div>
        <Metric label="买入" value={String(item.adjusted_buy_score)} tone="up" />
        <Metric label="卖出" value={String(item.adjusted_sell_score)} tone="down" />
        <Metric label="回测胜率" value={backtestSignalText(item)} tone={item.backtest_signal.score_adjustment >= 0 ? "up" : "down"} />
        <Metric label="排序修正" value={formatChange(item.backtest_signal.score_adjustment)} />
      </div>
    </button>
  );
}

function opportunityGroups(items: MonitorItem[]) {
  const buy = items.filter((item) => item.status === "偏买入机会");
  const sellPressure = items.filter((item) => item.status === "偏卖压风险");
  const sweep = items.filter((item) => item.status === "偏扫货拉升");
  const abnormal = items.filter(
    (item) =>
      item.status === "偏流动性异常" ||
      (item.status === "横盘观察" && Math.max(item.adjusted_buy_score, item.adjusted_sell_score) >= 70)
  );
  const grouped = new Set([...buy, ...sellPressure, ...sweep, ...abnormal].map((item) => item.id));
  const watch = items.filter((item) => !grouped.has(item.id));
  return [
    { title: "买入机会榜", items: sortOpportunities(buy) },
    { title: "卖压风险榜", items: sortOpportunities(sellPressure) },
    { title: "扫货拉升榜", items: sortOpportunities(sweep) },
    { title: "异常波动榜", items: sortOpportunities(abnormal) },
    { title: "观察候选", items: sortOpportunities(watch).slice(0, 8) },
  ];
}

function sortOpportunities(items: MonitorItem[]) {
  return [...items].sort(
    (a, b) => opportunityRankScore(b) - opportunityRankScore(a)
  );
}

function opportunityRankScore(item: MonitorItem) {
  return Math.max(item.adjusted_buy_score, item.adjusted_sell_score) + item.backtest_signal.score_adjustment;
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
      min_price_volatility_rate: strategy.min_price_volatility_rate,
      min_buy_change_rate: strategy.min_buy_change_rate,
      min_volume_change_rate: strategy.min_volume_change_rate,
      cooldown_minutes: strategy.cooldown_minutes,
      quality_penalty_max: strategy.quality_penalty_max,
      sell_fee_rate: strategy.sell_fee_rate,
      withdraw_fee_rate: strategy.withdraw_fee_rate,
      fx_rate: strategy.fx_rate
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
          label="价格波动率 %"
          value={toPercent(form.min_price_volatility_rate)}
          min={0.1}
          max={100}
          step={0.1}
          onChange={(value) => setForm({ ...form, min_price_volatility_rate: fromPercent(value) })}
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
          label="成交量变化率 %"
          value={toPercent(form.min_volume_change_rate)}
          min={1}
          max={1000}
          step={1}
          onChange={(value) => setForm({ ...form, min_volume_change_rate: fromPercent(value) })}
        />
        <NumberField
          label="冷却时间 分钟"
          value={form.cooldown_minutes}
          min={0}
          max={1440}
          step={1}
          onChange={(value) => setForm({ ...form, cooldown_minutes: value })}
        />
        <NumberField
          label="可信度最大降权"
          value={form.quality_penalty_max}
          min={0}
          max={100}
          step={1}
          onChange={(value) => setForm({ ...form, quality_penalty_max: value })}
        />
        <NumberField
          label="卖出手续费 %"
          value={toPercent(form.sell_fee_rate)}
          min={0}
          max={50}
          step={0.1}
          onChange={(value) => setForm({ ...form, sell_fee_rate: fromPercent(value) })}
        />
        <NumberField
          label="提现费率 %"
          value={toPercent(form.withdraw_fee_rate)}
          min={0}
          max={50}
          step={0.1}
          onChange={(value) => setForm({ ...form, withdraw_fee_rate: fromPercent(value) })}
        />
        <NumberField
          label="汇率/折算系数"
          value={form.fx_rate}
          min={0.01}
          max={100}
          step={0.01}
          onChange={(value) => setForm({ ...form, fx_rate: value })}
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
  collectRuns,
  opsHealth,
  opsReadiness,
  p0Summary,
  sourceConfig,
  sourceFieldQuality,
  retention
}: {
  items: MonitorItem[];
  pools: MonitorPool[];
  alerts: Alert[];
  pushRecords: PushRecord[];
  collectRuns: CollectRun[];
  opsHealth: OpsHealth | null;
  opsReadiness: OpsReadiness | null;
  p0Summary: P0Summary | null;
  sourceConfig: SourceConfig | null;
  sourceFieldQuality: SourceFieldQuality | null;
  retention: Retention | null;
}) {
  const hasSnapshots = items.some((item) => item.latest_snapshot);
  const latestPush = pushRecords[0];
  const latestRun = collectRuns[0];
  const qualityTotal = latestRun ? latestRun.real_field_count + latestRun.fallback_field_count : 0;
  const qualityRatio = qualityTotal ? latestRun!.real_field_count / qualityTotal : 0;
  const lowQualityItems = items.filter((item) => item.source_quality && item.source_quality.level !== "trusted");
  return (
    <section className="panel settings">
      <h2>数据源状态</h2>
      <div className="settings-grid">
        <Metric label="API 状态" value="在线" tone="up" />
        <Metric label="行情来源" value={sourceConfig ? sourceConfig.provider : "暂无"} tone={sourceConfigTone(sourceConfig?.readiness)} />
        <Metric label="订单簿" value={sourceConfig?.steam_orderbook_enabled ? "已开启" : "未开启"} tone={sourceConfig?.steam_orderbook_enabled ? "up" : "neutral"} />
        <Metric label="NameID 覆盖" value={sourceConfig ? `${sourceConfig.active_nameid_count}/${sourceConfig.active_item_count}` : "暂无"} tone={sourceConfig && sourceConfig.active_nameid_coverage_rate >= 0.8 ? "up" : "neutral"} />
        <Metric label="监控饰品" value={`${items.length} 个`} />
        <Metric label="监控池" value={`${pools.length} 个`} />
        <Metric label="运维状态" value={opsHealth ? opsStatusText(opsHealth.status) : "暂无"} tone={opsTone(opsHealth?.status)} />
        <Metric label="采集成功率" value={opsHealth ? formatPercent(opsHealth.collect_success_rate) : "暂无"} tone={opsHealth && opsHealth.collect_success_rate >= 0.8 ? "up" : "neutral"} />
        <Metric label="推送成功率" value={opsHealth ? formatPercent(opsHealth.push_success_rate) : "暂无"} tone={opsHealth && opsHealth.push_success_rate >= 0.8 ? "up" : "neutral"} />
        <Metric label="worker 延迟" value={opsHealth?.worker_lag_minutes == null ? "暂无" : `${opsHealth.worker_lag_minutes.toFixed(1)} 分钟`} tone={opsHealth?.status === "fail" ? "down" : "neutral"} />
        <Metric label="快照状态" value={hasSnapshots ? "已入库" : "待采集"} />
        <Metric label="24h 快照" value={opsHealth ? `${opsHealth.snapshot_count_24h} 条` : "暂无"} />
        <Metric label="24h 告警" value={opsHealth ? `${opsHealth.alert_count_24h} 条` : "暂无"} />
        <Metric label="24h 异常" value={opsHealth ? `${opsHealth.source_error_count_24h} 次` : "暂无"} tone={opsHealth && opsHealth.source_error_count_24h > 0 ? "down" : "neutral"} />
        <Metric label="最近告警" value={`${alerts.length} 条`} />
        <Metric label="最近采集" value={latestRun ? `${latestRun.status}:${latestRun.snapshot_count}` : "暂无"} />
        <Metric label="真实字段占比" value={opsHealth ? formatPercent(opsHealth.real_field_ratio_24h) : latestRun ? formatPercent(qualityRatio) : "暂无"} tone={(opsHealth?.real_field_ratio_24h ?? qualityRatio) > 0.5 ? "up" : "neutral"} />
        <Metric label="补位次数" value={latestRun ? `${latestRun.fallback_count} 次` : "暂无"} />
        <Metric label="最近推送" value={latestPush ? `${latestPush.channel}:${latestPush.status}` : "暂无"} />
        <Metric label="P0 观察天数" value={opsReadiness ? `${opsReadiness.observed_days.toFixed(1)} 天` : "暂无"} tone={opsReadiness?.ready_for_7d_review ? "up" : "neutral"} />
        <Metric label="P0 采集轮次" value={opsReadiness ? `${opsReadiness.success_run_count}/${opsReadiness.collect_run_count}` : "暂无"} tone={opsReadiness && opsReadiness.collect_success_rate >= 0.8 ? "up" : "neutral"} />
        <Metric label="快照覆盖率" value={opsReadiness ? formatPercent(opsReadiness.snapshot_coverage_rate) : "暂无"} tone={opsReadiness && opsReadiness.snapshot_coverage_rate >= 0.8 ? "up" : "neutral"} />
        <Metric label="7天复盘" value={opsReadiness?.ready_for_7d_review ? "可复盘" : "观察中"} tone={opsReadiness?.ready_for_7d_review ? "up" : "neutral"} />
        <Metric label="worker" value="本地手动采集 / Docker 常驻" />
      </div>
      <div className="push-table">
        <h3>P0 验证摘要</h3>
        {p0Summary ? (
          <>
            <div className="push-row">
              <span>{p0Summary.status}</span>
              <strong>{p0Summary.ready ? "可复盘" : "未就绪"}</strong>
              <span>{p0Summary.alert_count} 条告警</span>
              <span>{p0Summary.blockers.length ? p0Summary.blockers.join("；") : "暂无阻塞项"}</span>
            </div>
            {p0Summary.review_items.map((item) => (
              <div className="push-row" key={item}>
                <span>复盘项</span>
                <strong>{item}</strong>
              </div>
            ))}
          </>
        ) : (
          <div className="empty">暂无 P0 验证摘要</div>
        )}
      </div>
      <div className="push-table">
        <h3>数据源配置</h3>
        {sourceConfig ? (
          <div className="push-row">
            <span>{sourceConfig.readiness}</span>
            <strong>{formatPercent(sourceConfig.active_nameid_coverage_rate)}</strong>
            <span>环境映射 {sourceConfig.configured_nameid_count}</span>
            <span>{sourceConfig.suggestion}</span>
          </div>
        ) : (
          <div className="empty">暂无数据源配置</div>
        )}
      </div>
      <div className="push-table">
        <h3>字段真实率</h3>
        {sourceFieldQuality ? (
          sourceFieldQuality.fields.map((field) => (
            <div className="push-row" key={field.field}>
              <span>{field.label}</span>
              <strong>{formatPercent(field.real_ratio)}</strong>
              <span>真实 {field.real_count}</span>
              <span>补位 {field.fallback_count}</span>
              <span>样本 {sourceFieldQuality.snapshot_sample_count}</span>
            </div>
          ))
        ) : (
          <div className="empty">暂无字段质量数据</div>
        )}
      </div>
      <div className="push-table">
        <h3>低可信饰品</h3>
        {lowQualityItems.length ? (
          lowQualityItems.map((item) => (
            <div className="quality-row" key={item.id}>
              <strong>{item.display_name}</strong>
              <span>{qualityText(item)}</span>
              <span>{item.source_quality?.fallback_fields.join(", ") || "-"}</span>
            </div>
          ))
        ) : (
          <div className="empty">暂无低可信饰品</div>
        )}
      </div>
      <div className="push-table">
        <h3>数据保留策略</h3>
        {retention ? (
          retention.metrics.map((metric) => (
            <div className="push-row" key={metric.name}>
              <span>{metric.name}</span>
              <strong>{metric.policy}</strong>
              <span>{metric.row_count} 条</span>
              <span>{retentionDaysText(metric.retention_days)}</span>
              <span>{metric.oldest_at ? formatDate(metric.oldest_at) : "暂无"}</span>
            </div>
          ))
        ) : (
          <div className="empty">暂无保留策略</div>
        )}
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

function formatChange(value: number) {
  return `${value >= 0 ? "+" : ""}${value.toFixed(0)}`;
}

function retentionDaysText(days: number | null) {
  return days == null ? "长期" : `${days} 天`;
}

function strategyAdjustmentText(buy: number, sell: number) {
  return `买 ${formatChange(buy)} / 卖 ${formatChange(sell)}`;
}

function backtestSignalText(item: MonitorItem) {
  if (!item.backtest_signal.sample_count) {
    return "暂无";
  }
  return `${formatPercent(item.backtest_signal.win_rate)} / ${item.backtest_signal.sample_count}`;
}

function formatTime(value: string) {
  const date = new Date(value);
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  const hour = String(date.getHours()).padStart(2, "0");
  const minute = String(date.getMinutes()).padStart(2, "0");
  return `${month}-${day} ${hour}:${minute}`;
}

function formatDate(value: string) {
  const date = new Date(value);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  const hour = String(date.getHours()).padStart(2, "0");
  const minute = String(date.getMinutes()).padStart(2, "0");
  return `${year}-${month}-${day} ${hour}:${minute}`;
}

function batchMessage(
  label: string,
  result: {
    total: number;
    success_count: number;
    failure_count: number;
    results: Array<{ market_hash_name: string; ok: boolean; error: string }>;
  }
) {
  const failures = result.results
    .filter((row) => !row.ok)
    .slice(0, 3)
    .map((row) => `${row.market_hash_name}: ${row.error}`)
    .join("；");
  return `${label}完成：共 ${result.total}，成功 ${result.success_count}，失败 ${result.failure_count}${
    failures ? `。${failures}` : ""
  }`;
}

function qualityText(item: MonitorItem | ItemDetail) {
  if (!item.source_quality) {
    return "待采集";
  }
  return `${Math.round(item.source_quality.real_ratio * 100)}% ${qualityLevelText(item.source_quality.level)}`;
}

function qualityLevelText(level: string) {
  if (level === "trusted") {
    return "可信";
  }
  if (level === "partial") {
    return "部分补位";
  }
  return "补位";
}

function opsStatusText(status: string) {
  if (status === "ok") {
    return "正常";
  }
  if (status === "fail") {
    return "故障";
  }
  return "预警";
}

function opsTone(status?: string) {
  if (status === "ok") {
    return "up";
  }
  if (status === "fail") {
    return "down";
  }
  return "neutral";
}

function sourceConfigTone(readiness?: string) {
  if (readiness === "ready") {
    return "up";
  }
  if (readiness === "partial") {
    return "neutral";
  }
  return "down";
}

function confidenceClass(level: string) {
  if (level === "高") {
    return "trusted";
  }
  if (level === "中") {
    return "partial";
  }
  return "fallback";
}

function suggestionClass(action: string) {
  if (action === "适度放宽") {
    return "trusted";
  }
  if (action === "收紧阈值") {
    return "fallback";
  }
  return "partial";
}

function signalClass(action: string) {
  if (action === "买入") {
    return "buy";
  }
  if (action === "卖出") {
    return "sell";
  }
  if (action === "持有") {
    return "hold";
  }
  return "watch";
}

function signalTone(action: string) {
  if (action === "买入") {
    return "up";
  }
  if (action === "卖出") {
    return "down";
  }
  return "neutral";
}

function scoreLabel(adjusted: number, raw: number) {
  return adjusted === raw ? String(adjusted) : `${adjusted} / 原 ${raw}`;
}
