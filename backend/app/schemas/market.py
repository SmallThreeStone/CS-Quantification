from datetime import datetime

from pydantic import BaseModel


class SnapshotOut(BaseModel):
    id: int
    lowest_price: float
    sell_count: int
    highest_buy_price: float
    buy_count: int
    volume_24h: int
    avg_price_24h: float
    captured_at: datetime

    model_config = {"from_attributes": True}


class AlertOut(BaseModel):
    id: int
    item_id: int
    platform_id: int
    alert_type: str
    severity: str
    direction: str
    title: str
    detail: str
    previous_value: float
    current_value: float
    absolute_change: float
    change_rate: float
    created_at: datetime
    item_name: str
    platform_name: str


class PushRecordOut(BaseModel):
    id: int
    alert_id: int
    channel: str
    status: str
    target: str
    error: str
    created_at: datetime
    sent_at: datetime | None

    model_config = {"from_attributes": True}


class MonitorItemOut(BaseModel):
    id: int
    display_name: str
    market_hash_name: str
    exterior: str
    category: str
    status: str
    buy_score: int
    sell_score: int
    latest_snapshot: SnapshotOut | None
    latest_alert: AlertOut | None


class ItemDetailOut(BaseModel):
    id: int
    display_name: str
    market_hash_name: str
    exterior: str
    category: str
    status: str
    buy_score: int
    sell_score: int
    snapshots: list[SnapshotOut]
    alerts: list[AlertOut]


class HealthOut(BaseModel):
    status: str
    service: str
    version: str
