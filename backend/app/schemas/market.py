from datetime import datetime

from pydantic import BaseModel, Field


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


class BacktestResultOut(BaseModel):
    id: int
    alert_id: int
    item_id: int
    platform_id: int
    horizon_minutes: int
    entry_price: float
    exit_price: float
    price_change: float
    change_rate: float
    evaluated_at: datetime
    created_at: datetime
    item_name: str
    alert_type: str
    direction: str


class BacktestSummaryOut(BaseModel):
    alert_type: str
    horizon_minutes: int
    sample_count: int
    win_count: int
    win_rate: float
    avg_change_rate: float


class StrategyConfigOut(BaseModel):
    id: int
    name: str
    min_absolute_sell_change: int
    min_sell_change_rate: float
    min_price_change_rate: float
    min_buy_change_rate: float
    cooldown_minutes: int

    model_config = {"from_attributes": True}


class StrategyConfigUpdate(BaseModel):
    min_absolute_sell_change: int = Field(ge=1, le=10000)
    min_sell_change_rate: float = Field(ge=0.01, le=5)
    min_price_change_rate: float = Field(ge=0.001, le=1)
    min_buy_change_rate: float = Field(ge=0.01, le=5)
    cooldown_minutes: int = Field(ge=0, le=1440)


class ItemOut(BaseModel):
    id: int
    market_hash_name: str
    display_name: str
    exterior: str
    category: str
    is_active: bool
    pool_id: int | None
    pool_name: str | None = None

    model_config = {"from_attributes": True}


class ItemCreate(BaseModel):
    market_hash_name: str = Field(min_length=3, max_length=240)
    display_name: str = Field(min_length=1, max_length=160)
    exterior: str = Field(default="", max_length=80)
    category: str = Field(default="", max_length=80)
    is_active: bool = True
    pool_id: int | None = None


class ItemUpdate(BaseModel):
    market_hash_name: str = Field(min_length=3, max_length=240)
    display_name: str = Field(min_length=1, max_length=160)
    exterior: str = Field(default="", max_length=80)
    category: str = Field(default="", max_length=80)
    is_active: bool = True
    pool_id: int | None = None


class MonitorPoolOut(BaseModel):
    id: int
    name: str
    interval_minutes: int
    description: str
    last_collected_at: datetime | None
    active_item_count: int


class MonitorItemOut(BaseModel):
    id: int
    display_name: str
    market_hash_name: str
    exterior: str
    category: str
    pool_name: str | None
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
