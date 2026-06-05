import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Alert, BacktestResult, CollectRunLog, Item, MarketSnapshot, MonitorPool, Platform, PushRecord
from app.models import StrategyConfig
from app.schemas.market import (
    AlertOut,
    BacktestResultOut,
    BacktestSummaryOut,
    CollectRunLogOut,
    DecisionSignalOut,
    AlertSummaryOut,
    HeatmapBucketOut,
    HealthOut,
    HistoryPointOut,
    ItemCreate,
    ItemDetailOut,
    ItemOut,
    ItemUpdate,
    SteamOrderbookValidationOut,
    SteamNameIdBatchOut,
    SteamNameIdOut,
    MonitorPoolCreate,
    MonitorPoolOut,
    MonitorPoolUpdate,
    MonitorItemOut,
    PushRecordOut,
    SnapshotOut,
    SourceQualityOut,
    StrategyConfigOut,
    StrategyConfigUpdate,
)
from app.services.market_service import MarketService
from app.services.backtest_service import BacktestService
from app.services.push_service import PushService
from app.services.score_service import decision_from_scores, score_from_snapshot, status_from_alert
from app.services.steam_nameid_service import SteamNameIdService

router = APIRouter()


@router.get("/health", response_model=HealthOut)
def health() -> HealthOut:
    return HealthOut(status="ok", service="cs-quantification-api", version="0.1")


@router.post("/collect", response_model=list[AlertOut])
def collect(db: Session = Depends(get_db)) -> list[AlertOut]:
    market_service = MarketService(db)
    alerts = market_service.collect_active_items()
    PushService(db).dispatch_alerts(alerts)
    BacktestService(db).evaluate_due_alerts()
    return [_alert_out(alert) for alert in alerts]


@router.get("/monitor", response_model=list[MonitorItemOut])
def monitor(db: Session = Depends(get_db)) -> list[MonitorItemOut]:
    items = db.query(Item).filter_by(is_active=True).order_by(Item.display_name.asc()).all()
    config = _default_strategy(db)
    return [_monitor_item(db, item, config) for item in items]


@router.get("/items", response_model=list[ItemOut])
def item_list(db: Session = Depends(get_db)) -> list[ItemOut]:
    items = db.query(Item).order_by(Item.is_active.desc(), Item.display_name.asc()).all()
    return [_item_out(item) for item in items]


@router.post("/items", response_model=ItemOut)
def create_item(payload: ItemCreate, db: Session = Depends(get_db)) -> ItemOut:
    existing = db.query(Item).filter_by(market_hash_name=payload.market_hash_name).first()
    if existing is not None:
        raise HTTPException(status_code=409, detail="item already exists")
    _ensure_pool(db, payload.pool_id)
    item = Item(
        market_hash_name=payload.market_hash_name,
        display_name=payload.display_name,
        exterior=payload.exterior,
        category=payload.category,
        steam_item_nameid=payload.steam_item_nameid,
        is_active=payload.is_active,
        pool_id=payload.pool_id,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return _item_out(item)


@router.get("/items/{item_id}", response_model=ItemDetailOut)
def item_detail(item_id: int, db: Session = Depends(get_db)) -> ItemDetailOut:
    item = db.get(Item, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="item not found")
    snapshots = (
        db.query(MarketSnapshot)
        .filter(MarketSnapshot.item_id == item_id)
        .order_by(MarketSnapshot.captured_at.desc())
        .limit(120)
        .all()
    )
    alerts = db.query(Alert).filter(Alert.item_id == item_id).order_by(Alert.created_at.desc()).limit(30).all()
    latest_snapshot = snapshots[0] if snapshots else None
    latest_alert = alerts[0] if alerts else None
    buy_score, sell_score = score_from_snapshot(latest_snapshot, latest_alert)
    source_quality = _source_quality(latest_snapshot)
    config = _default_strategy(db)
    adjusted_buy_score, adjusted_sell_score, quality_penalty = _quality_adjusted_scores(
        buy_score, sell_score, source_quality, config.quality_penalty_max
    )
    status = status_from_alert(latest_alert)
    decision_signal = _decision_signal(latest_snapshot, status, adjusted_buy_score, adjusted_sell_score, source_quality)
    return ItemDetailOut(
        id=item.id,
        display_name=item.display_name,
        market_hash_name=item.market_hash_name,
        exterior=item.exterior,
        category=item.category,
        steam_item_nameid=item.steam_item_nameid,
        status=status,
        buy_score=buy_score,
        sell_score=sell_score,
        adjusted_buy_score=adjusted_buy_score,
        adjusted_sell_score=adjusted_sell_score,
        quality_penalty=quality_penalty,
        snapshots=[SnapshotOut.model_validate(snapshot) for snapshot in reversed(snapshots)],
        alerts=[_alert_out(alert) for alert in alerts],
        heatmap=_heatmap(list(reversed(snapshots))),
        alert_summary=_alert_summary(alerts),
        source_quality=source_quality,
        decision_signal=decision_signal,
    )


@router.get("/items/{item_id}/history/price", response_model=list[HistoryPointOut])
def item_price_history(item_id: int, limit: int = Query(default=240, ge=1, le=5000), db: Session = Depends(get_db)) -> list[HistoryPointOut]:
    _ensure_item(db, item_id)
    return _history_points(db, item_id, "lowest_price", limit)


@router.get("/items/{item_id}/history/sell", response_model=list[HistoryPointOut])
def item_sell_history(item_id: int, limit: int = Query(default=240, ge=1, le=5000), db: Session = Depends(get_db)) -> list[HistoryPointOut]:
    _ensure_item(db, item_id)
    return _history_points(db, item_id, "sell_count", limit)


@router.get("/items/{item_id}/history/buy", response_model=list[HistoryPointOut])
def item_buy_history(item_id: int, limit: int = Query(default=240, ge=1, le=5000), db: Session = Depends(get_db)) -> list[HistoryPointOut]:
    _ensure_item(db, item_id)
    return _history_points(db, item_id, "buy_count", limit)


@router.put("/items/{item_id}", response_model=ItemOut)
def update_item(item_id: int, payload: ItemUpdate, db: Session = Depends(get_db)) -> ItemOut:
    item = db.get(Item, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="item not found")
    duplicate = db.query(Item).filter(Item.market_hash_name == payload.market_hash_name, Item.id != item_id).first()
    if duplicate is not None:
        raise HTTPException(status_code=409, detail="item already exists")
    _ensure_pool(db, payload.pool_id)
    item.market_hash_name = payload.market_hash_name
    item.display_name = payload.display_name
    item.exterior = payload.exterior
    item.category = payload.category
    item.steam_item_nameid = payload.steam_item_nameid
    item.is_active = payload.is_active
    item.pool_id = payload.pool_id
    db.commit()
    db.refresh(item)
    return _item_out(item)


@router.patch("/items/{item_id}/active", response_model=ItemOut)
def set_item_active(item_id: int, is_active: bool, db: Session = Depends(get_db)) -> ItemOut:
    item = db.get(Item, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="item not found")
    item.is_active = is_active
    db.commit()
    db.refresh(item)
    return _item_out(item)


@router.post("/items/{item_id}/steam-nameid/discover", response_model=SteamNameIdOut)
def discover_item_steam_nameid(item_id: int, db: Session = Depends(get_db)) -> SteamNameIdOut:
    item = db.get(Item, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="item not found")
    try:
        _discover_nameid(item, db, SteamNameIdService())
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return SteamNameIdOut(
        item_id=item.id,
        market_hash_name=item.market_hash_name,
        steam_item_nameid=item.steam_item_nameid,
    )


@router.post("/steam-nameids/discover-missing", response_model=SteamNameIdBatchOut)
def discover_missing_steam_nameids(db: Session = Depends(get_db)) -> SteamNameIdBatchOut:
    service = SteamNameIdService()
    items = (
        db.query(Item)
        .filter(Item.is_active.is_(True), (Item.steam_item_nameid == "") | (Item.steam_item_nameid.is_(None)))
        .order_by(Item.display_name.asc())
        .all()
    )
    results: list[SteamOrderbookValidationOut] = []
    for item in items:
        try:
            _discover_nameid(item, db, service)
            results.append(_validation_result(item, ok=True))
        except Exception as exc:
            db.rollback()
            results.append(_validation_result(item, ok=False, error=str(exc)))
    return _batch_result(results)


@router.post("/items/{item_id}/steam-nameid/validate", response_model=SteamOrderbookValidationOut)
def validate_item_steam_nameid(item_id: int, db: Session = Depends(get_db)) -> SteamOrderbookValidationOut:
    item = db.get(Item, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="item not found")
    return _validate_nameid(item, SteamNameIdService())


@router.post("/steam-nameids/validate-all", response_model=SteamNameIdBatchOut)
def validate_all_steam_nameids(db: Session = Depends(get_db)) -> SteamNameIdBatchOut:
    service = SteamNameIdService()
    items = (
        db.query(Item)
        .filter(Item.is_active.is_(True), Item.steam_item_nameid != "")
        .order_by(Item.display_name.asc())
        .all()
    )
    results = [_validate_nameid(item, service) for item in items]
    return _batch_result(results)


def _discover_nameid(item: Item, db: Session, service: SteamNameIdService) -> None:
    item.steam_item_nameid = service.discover(item.market_hash_name)
    db.commit()
    db.refresh(item)


def _validate_nameid(item: Item, service: SteamNameIdService) -> SteamOrderbookValidationOut:
    try:
        orderbook = service.validate_orderbook(item.steam_item_nameid)
    except Exception as exc:
        return _validation_result(item, ok=False, error=str(exc))
    return _validation_result(
        item,
        ok=True,
        sell_count=orderbook["sell_count"],
        buy_count=orderbook["buy_count"],
        highest_buy_price=orderbook["highest_buy_price"],
    )


def _validation_result(
    item: Item,
    ok: bool,
    sell_count: int = 0,
    buy_count: int = 0,
    highest_buy_price: float = 0,
    error: str = "",
) -> SteamOrderbookValidationOut:
    return SteamOrderbookValidationOut(
        item_id=item.id,
        market_hash_name=item.market_hash_name,
        steam_item_nameid=item.steam_item_nameid,
        ok=ok,
        sell_count=sell_count,
        buy_count=buy_count,
        highest_buy_price=highest_buy_price,
        error=error,
    )


def _batch_result(results: list[SteamOrderbookValidationOut]) -> SteamNameIdBatchOut:
    success_count = sum(1 for result in results if result.ok)
    return SteamNameIdBatchOut(
        total=len(results),
        success_count=success_count,
        failure_count=len(results) - success_count,
        results=results,
    )


@router.get("/monitor-pools", response_model=list[MonitorPoolOut])
def monitor_pools(db: Session = Depends(get_db)) -> list[MonitorPoolOut]:
    pools = db.query(MonitorPool).order_by(MonitorPool.interval_minutes.asc()).all()
    return [_monitor_pool_out(pool) for pool in pools]


@router.post("/monitor-pools", response_model=MonitorPoolOut)
def create_monitor_pool(payload: MonitorPoolCreate, db: Session = Depends(get_db)) -> MonitorPoolOut:
    if db.query(MonitorPool).filter_by(name=payload.name).first() is not None:
        raise HTTPException(status_code=409, detail="monitor pool already exists")
    pool = MonitorPool(
        name=payload.name,
        interval_minutes=payload.interval_minutes,
        description=payload.description,
    )
    db.add(pool)
    db.commit()
    db.refresh(pool)
    return _monitor_pool_out(pool)


@router.put("/monitor-pools/{pool_id}", response_model=MonitorPoolOut)
def update_monitor_pool(pool_id: int, payload: MonitorPoolUpdate, db: Session = Depends(get_db)) -> MonitorPoolOut:
    pool = db.get(MonitorPool, pool_id)
    if pool is None:
        raise HTTPException(status_code=404, detail="monitor pool not found")
    duplicate = db.query(MonitorPool).filter(MonitorPool.name == payload.name, MonitorPool.id != pool_id).first()
    if duplicate is not None:
        raise HTTPException(status_code=409, detail="monitor pool already exists")
    pool.name = payload.name
    pool.interval_minutes = payload.interval_minutes
    pool.description = payload.description
    db.commit()
    db.refresh(pool)
    return _monitor_pool_out(pool)


def _monitor_pool_out(pool: MonitorPool) -> MonitorPoolOut:
    return MonitorPoolOut(
        id=pool.id,
        name=pool.name,
        interval_minutes=pool.interval_minutes,
        description=pool.description,
        last_collected_at=pool.last_collected_at,
        active_item_count=sum(1 for item in pool.items if item.is_active),
    )


@router.get("/collect-runs", response_model=list[CollectRunLogOut])
def collect_runs(db: Session = Depends(get_db)) -> list[CollectRunLog]:
    return db.query(CollectRunLog).order_by(CollectRunLog.started_at.desc()).limit(100).all()


@router.get("/alerts", response_model=list[AlertOut])
def alerts(
    item: str = Query(default=""),
    alert_type: str = Query(default=""),
    severity: str = Query(default=""),
    platform: str = Query(default=""),
    db: Session = Depends(get_db),
) -> list[AlertOut]:
    query = db.query(Alert).join(Item, Alert.item_id == Item.id).join(Platform, Alert.platform_id == Platform.id)
    if item:
        query = query.filter(Item.display_name.contains(item))
    if alert_type:
        query = query.filter(Alert.alert_type == alert_type)
    if severity:
        query = query.filter(Alert.severity == severity)
    if platform:
        query = query.filter(Platform.name.contains(platform))
    rows = query.order_by(Alert.created_at.desc()).limit(100).all()
    return [_alert_out(alert) for alert in rows]


@router.get("/push-records", response_model=list[PushRecordOut])
def push_records(db: Session = Depends(get_db)) -> list[PushRecordOut]:
    return db.query(PushRecord).order_by(PushRecord.created_at.desc()).limit(100).all()


@router.get("/backtests", response_model=list[BacktestResultOut])
def backtests(db: Session = Depends(get_db)) -> list[BacktestResultOut]:
    rows = db.query(BacktestResult).order_by(BacktestResult.created_at.desc()).limit(200).all()
    return [_backtest_out(row) for row in rows]


@router.get("/backtests/summary", response_model=list[BacktestSummaryOut])
def backtest_summary(db: Session = Depends(get_db)) -> list[dict]:
    return BacktestService(db).summary()


@router.post("/backtests/evaluate", response_model=list[BacktestResultOut])
def evaluate_backtests(db: Session = Depends(get_db)) -> list[BacktestResultOut]:
    rows = BacktestService(db).evaluate_due_alerts()
    return [_backtest_out(row) for row in rows]


@router.get("/strategy", response_model=StrategyConfigOut)
def strategy(db: Session = Depends(get_db)) -> StrategyConfig:
    return _default_strategy(db)


@router.put("/strategy", response_model=StrategyConfigOut)
def update_strategy(payload: StrategyConfigUpdate, db: Session = Depends(get_db)) -> StrategyConfig:
    config = _default_strategy(db)
    config.min_absolute_sell_change = payload.min_absolute_sell_change
    config.min_sell_change_rate = payload.min_sell_change_rate
    config.min_price_change_rate = payload.min_price_change_rate
    config.min_price_volatility_rate = payload.min_price_volatility_rate
    config.min_buy_change_rate = payload.min_buy_change_rate
    config.min_volume_change_rate = payload.min_volume_change_rate
    config.cooldown_minutes = payload.cooldown_minutes
    config.quality_penalty_max = payload.quality_penalty_max
    db.commit()
    db.refresh(config)
    return config


@router.get("/opportunities", response_model=list[MonitorItemOut])
def opportunities(db: Session = Depends(get_db)) -> list[MonitorItemOut]:
    config = _default_strategy(db)
    items = [_monitor_item(db, item, config) for item in db.query(Item).filter_by(is_active=True).all()]
    return sorted(items, key=lambda row: max(row.adjusted_buy_score, row.adjusted_sell_score), reverse=True)


def _monitor_item(db: Session, item: Item, config: StrategyConfig) -> MonitorItemOut:
    latest_snapshot = (
        db.query(MarketSnapshot)
        .filter(MarketSnapshot.item_id == item.id)
        .order_by(MarketSnapshot.captured_at.desc())
        .first()
    )
    latest_alert = db.query(Alert).filter(Alert.item_id == item.id).order_by(Alert.created_at.desc()).first()
    buy_score, sell_score = score_from_snapshot(latest_snapshot, latest_alert)
    source_quality = _source_quality(latest_snapshot)
    adjusted_buy_score, adjusted_sell_score, quality_penalty = _quality_adjusted_scores(
        buy_score, sell_score, source_quality, config.quality_penalty_max
    )
    status = status_from_alert(latest_alert)
    decision_signal = _decision_signal(latest_snapshot, status, adjusted_buy_score, adjusted_sell_score, source_quality)
    return MonitorItemOut(
        id=item.id,
        display_name=item.display_name,
        market_hash_name=item.market_hash_name,
        exterior=item.exterior,
        category=item.category,
        steam_item_nameid=item.steam_item_nameid,
        pool_name=item.pool.name if item.pool else None,
        status=status,
        buy_score=buy_score,
        sell_score=sell_score,
        adjusted_buy_score=adjusted_buy_score,
        adjusted_sell_score=adjusted_sell_score,
        quality_penalty=quality_penalty,
        latest_snapshot=SnapshotOut.model_validate(latest_snapshot) if latest_snapshot else None,
        latest_alert=_alert_out(latest_alert) if latest_alert else None,
        source_quality=source_quality,
        decision_signal=decision_signal,
    )


def _alert_out(alert: Alert) -> AlertOut:
    platform = alert.platform or Platform(name="Unknown", code="unknown")
    return AlertOut(
        id=alert.id,
        item_id=alert.item_id,
        platform_id=alert.platform_id,
        alert_type=alert.alert_type,
        severity=alert.severity,
        direction=alert.direction,
        title=alert.title,
        detail=alert.detail,
        previous_value=alert.previous_value,
        current_value=alert.current_value,
        absolute_change=alert.absolute_change,
        change_rate=alert.change_rate,
        created_at=alert.created_at,
        item_name=alert.item.display_name,
        platform_name=platform.name,
    )


def _item_out(item: Item) -> ItemOut:
    return ItemOut(
        id=item.id,
        market_hash_name=item.market_hash_name,
        display_name=item.display_name,
        exterior=item.exterior,
        category=item.category,
        steam_item_nameid=item.steam_item_nameid,
        is_active=item.is_active,
        pool_id=item.pool_id,
        pool_name=item.pool.name if item.pool else None,
    )


def _backtest_out(row: BacktestResult) -> BacktestResultOut:
    return BacktestResultOut(
        id=row.id,
        alert_id=row.alert_id,
        item_id=row.item_id,
        platform_id=row.platform_id,
        horizon_minutes=row.horizon_minutes,
        entry_price=row.entry_price,
        exit_price=row.exit_price,
        price_change=row.price_change,
        change_rate=row.change_rate,
        evaluated_at=row.evaluated_at,
        created_at=row.created_at,
        item_name=row.item.display_name,
        alert_type=row.alert.alert_type,
        direction=row.alert.direction,
    )


def _heatmap(snapshots: list[MarketSnapshot]) -> list[HeatmapBucketOut]:
    buckets: dict[int, dict[str, float]] = {}
    previous_by_hour: dict[int, MarketSnapshot] = {}
    for snapshot in snapshots:
        hour = snapshot.captured_at.hour
        bucket = buckets.setdefault(
            hour,
            {
                "snapshot_count": 0,
                "sell_count": 0,
                "buy_count": 0,
                "volume_24h": 0,
                "lowest_price": 0,
                "max_sell_change": 0,
                "max_buy_change": 0,
            },
        )
        bucket["snapshot_count"] += 1
        bucket["sell_count"] += snapshot.sell_count
        bucket["buy_count"] += snapshot.buy_count
        bucket["volume_24h"] += snapshot.volume_24h
        bucket["lowest_price"] += snapshot.lowest_price
        previous = previous_by_hour.get(hour)
        if previous is not None:
            bucket["max_sell_change"] = max(bucket["max_sell_change"], abs(snapshot.sell_count - previous.sell_count))
            bucket["max_buy_change"] = max(bucket["max_buy_change"], abs(snapshot.buy_count - previous.buy_count))
        previous_by_hour[hour] = snapshot
    return [
        HeatmapBucketOut(
            hour=hour,
            snapshot_count=int(row["snapshot_count"]),
            avg_sell_count=row["sell_count"] / row["snapshot_count"],
            avg_buy_count=row["buy_count"] / row["snapshot_count"],
            avg_volume_24h=row["volume_24h"] / row["snapshot_count"],
            avg_lowest_price=row["lowest_price"] / row["snapshot_count"],
            max_sell_change=row["max_sell_change"],
            max_buy_change=row["max_buy_change"],
        )
        for hour, row in sorted(buckets.items())
    ]


def _alert_summary(alerts: list[Alert]) -> list[AlertSummaryOut]:
    grouped: dict[str, list[Alert]] = {}
    for alert in alerts:
        grouped.setdefault(alert.alert_type, []).append(alert)
    return [
        AlertSummaryOut(
            alert_type=alert_type,
            total_count=len(rows),
            recent_alerts=[_alert_out(alert) for alert in rows[:3]],
        )
        for alert_type, rows in sorted(grouped.items(), key=lambda item: len(item[1]), reverse=True)
    ]


def _source_quality(snapshot: MarketSnapshot | None) -> SourceQualityOut | None:
    if snapshot is None:
        return None
    try:
        payload = json.loads(snapshot.raw_payload or "{}")
    except json.JSONDecodeError:
        return None
    quality = payload.get("source_quality") or {}
    real_fields = list(quality.get("real_fields") or [])
    fallback_fields = list(quality.get("fallback_fields") or [])
    total = len(real_fields) + len(fallback_fields)
    real_ratio = len(real_fields) / total if total else 0
    if real_ratio >= 0.8:
        level = "trusted"
    elif real_ratio > 0:
        level = "partial"
    else:
        level = "fallback"
    return SourceQualityOut(
        real_fields=real_fields,
        fallback_fields=fallback_fields,
        real_field_count=len(real_fields),
        fallback_field_count=len(fallback_fields),
        real_ratio=real_ratio,
        level=level,
    )


def _quality_adjusted_scores(
    buy_score: int,
    sell_score: int,
    source_quality: SourceQualityOut | None,
    max_penalty: int,
) -> tuple[int, int, int]:
    if source_quality is None:
        penalty = round(max_penalty / 2)
        return max(0, buy_score - penalty), max(0, sell_score - penalty), penalty
    penalty = round((1 - source_quality.real_ratio) * max_penalty)
    return max(0, buy_score - penalty), max(0, sell_score - penalty), penalty


def _decision_signal(
    snapshot: MarketSnapshot | None,
    status: str,
    adjusted_buy_score: int,
    adjusted_sell_score: int,
    source_quality: SourceQualityOut | None,
) -> DecisionSignalOut:
    signal = decision_from_scores(
        snapshot,
        status,
        adjusted_buy_score,
        adjusted_sell_score,
        source_quality.real_ratio if source_quality else None,
    )
    return DecisionSignalOut(**signal)


def _ensure_pool(db: Session, pool_id: int | None) -> None:
    if pool_id is not None and db.get(MonitorPool, pool_id) is None:
        raise HTTPException(status_code=404, detail="monitor pool not found")


def _ensure_item(db: Session, item_id: int) -> None:
    if db.get(Item, item_id) is None:
        raise HTTPException(status_code=404, detail="item not found")


def _history_points(db: Session, item_id: int, field: str, limit: int) -> list[HistoryPointOut]:
    rows = (
        db.query(MarketSnapshot)
        .filter(MarketSnapshot.item_id == item_id)
        .order_by(MarketSnapshot.captured_at.desc())
        .limit(limit)
        .all()
    )
    return [
        HistoryPointOut(captured_at=snapshot.captured_at, value=float(getattr(snapshot, field)))
        for snapshot in reversed(rows)
    ]


def _default_strategy(db: Session) -> StrategyConfig:
    config = db.query(StrategyConfig).filter_by(name="default").first()
    if config is None:
        config = StrategyConfig(name="default")
        db.add(config)
        db.commit()
        db.refresh(config)
    return config
