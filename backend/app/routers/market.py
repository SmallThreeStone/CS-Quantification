from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Alert, BacktestResult, CollectRunLog, Item, MarketSnapshot, MonitorPool, Platform, PushRecord
from app.models import StrategyConfig
from app.schemas.market import (
    AlertOut,
    BacktestResultOut,
    BacktestSummaryOut,
    CollectRunLogOut,
    AlertSummaryOut,
    HeatmapBucketOut,
    HealthOut,
    ItemCreate,
    ItemDetailOut,
    ItemOut,
    ItemUpdate,
    MonitorPoolOut,
    MonitorItemOut,
    PushRecordOut,
    SnapshotOut,
    StrategyConfigOut,
    StrategyConfigUpdate,
)
from app.services.market_service import MarketService
from app.services.backtest_service import BacktestService
from app.services.push_service import PushService
from app.services.score_service import score_from_snapshot, status_from_alert

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
    return [_monitor_item(db, item) for item in items]


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
    return ItemDetailOut(
        id=item.id,
        display_name=item.display_name,
        market_hash_name=item.market_hash_name,
        exterior=item.exterior,
        category=item.category,
        steam_item_nameid=item.steam_item_nameid,
        status=status_from_alert(latest_alert),
        buy_score=buy_score,
        sell_score=sell_score,
        snapshots=[SnapshotOut.model_validate(snapshot) for snapshot in reversed(snapshots)],
        alerts=[_alert_out(alert) for alert in alerts],
        heatmap=_heatmap(list(reversed(snapshots))),
        alert_summary=_alert_summary(alerts),
    )


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


@router.get("/monitor-pools", response_model=list[MonitorPoolOut])
def monitor_pools(db: Session = Depends(get_db)) -> list[MonitorPoolOut]:
    pools = db.query(MonitorPool).order_by(MonitorPool.interval_minutes.asc()).all()
    return [
        MonitorPoolOut(
            id=pool.id,
            name=pool.name,
            interval_minutes=pool.interval_minutes,
            description=pool.description,
            last_collected_at=pool.last_collected_at,
            active_item_count=sum(1 for item in pool.items if item.is_active),
        )
        for pool in pools
    ]


@router.get("/collect-runs", response_model=list[CollectRunLogOut])
def collect_runs(db: Session = Depends(get_db)) -> list[CollectRunLog]:
    return db.query(CollectRunLog).order_by(CollectRunLog.started_at.desc()).limit(100).all()


@router.get("/alerts", response_model=list[AlertOut])
def alerts(db: Session = Depends(get_db)) -> list[AlertOut]:
    rows = db.query(Alert).order_by(Alert.created_at.desc()).limit(100).all()
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
    config.min_buy_change_rate = payload.min_buy_change_rate
    config.cooldown_minutes = payload.cooldown_minutes
    db.commit()
    db.refresh(config)
    return config


@router.get("/opportunities", response_model=list[MonitorItemOut])
def opportunities(db: Session = Depends(get_db)) -> list[MonitorItemOut]:
    items = [_monitor_item(db, item) for item in db.query(Item).filter_by(is_active=True).all()]
    return sorted(items, key=lambda row: max(row.buy_score, row.sell_score), reverse=True)


def _monitor_item(db: Session, item: Item) -> MonitorItemOut:
    latest_snapshot = (
        db.query(MarketSnapshot)
        .filter(MarketSnapshot.item_id == item.id)
        .order_by(MarketSnapshot.captured_at.desc())
        .first()
    )
    latest_alert = db.query(Alert).filter(Alert.item_id == item.id).order_by(Alert.created_at.desc()).first()
    buy_score, sell_score = score_from_snapshot(latest_snapshot, latest_alert)
    return MonitorItemOut(
        id=item.id,
        display_name=item.display_name,
        market_hash_name=item.market_hash_name,
        exterior=item.exterior,
        category=item.category,
        steam_item_nameid=item.steam_item_nameid,
        pool_name=item.pool.name if item.pool else None,
        status=status_from_alert(latest_alert),
        buy_score=buy_score,
        sell_score=sell_score,
        latest_snapshot=SnapshotOut.model_validate(latest_snapshot) if latest_snapshot else None,
        latest_alert=_alert_out(latest_alert) if latest_alert else None,
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


def _ensure_pool(db: Session, pool_id: int | None) -> None:
    if pool_id is not None and db.get(MonitorPool, pool_id) is None:
        raise HTTPException(status_code=404, detail="monitor pool not found")


def _default_strategy(db: Session) -> StrategyConfig:
    config = db.query(StrategyConfig).filter_by(name="default").first()
    if config is None:
        config = StrategyConfig(name="default")
        db.add(config)
        db.commit()
        db.refresh(config)
    return config
