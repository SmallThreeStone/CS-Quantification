from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Alert, Item, MarketSnapshot, Platform, PushRecord
from app.schemas.market import AlertOut, HealthOut, ItemDetailOut, MonitorItemOut, PushRecordOut, SnapshotOut
from app.services.market_service import MarketService
from app.services.push_service import PushService
from app.services.score_service import score_from_snapshot, status_from_alert

router = APIRouter()


@router.get("/health", response_model=HealthOut)
def health() -> HealthOut:
    return HealthOut(status="ok", service="cs-quantification-api", version="0.1")


@router.post("/collect", response_model=list[AlertOut])
def collect(db: Session = Depends(get_db)) -> list[AlertOut]:
    alerts = MarketService(db).collect_active_items()
    PushService(db).dispatch_alerts(alerts)
    return [_alert_out(alert) for alert in alerts]


@router.get("/monitor", response_model=list[MonitorItemOut])
def monitor(db: Session = Depends(get_db)) -> list[MonitorItemOut]:
    items = db.query(Item).filter_by(is_active=True).order_by(Item.display_name.asc()).all()
    return [_monitor_item(db, item) for item in items]


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
        status=status_from_alert(latest_alert),
        buy_score=buy_score,
        sell_score=sell_score,
        snapshots=[SnapshotOut.model_validate(snapshot) for snapshot in reversed(snapshots)],
        alerts=[_alert_out(alert) for alert in alerts],
    )


@router.get("/alerts", response_model=list[AlertOut])
def alerts(db: Session = Depends(get_db)) -> list[AlertOut]:
    rows = db.query(Alert).order_by(Alert.created_at.desc()).limit(100).all()
    return [_alert_out(alert) for alert in rows]


@router.get("/push-records", response_model=list[PushRecordOut])
def push_records(db: Session = Depends(get_db)) -> list[PushRecordOut]:
    return db.query(PushRecord).order_by(PushRecord.created_at.desc()).limit(100).all()


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
