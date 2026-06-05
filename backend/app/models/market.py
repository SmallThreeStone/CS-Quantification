from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Platform(Base):
    __tablename__ = "platforms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(80))


class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    market_hash_name: Mapped[str] = mapped_column(String(240), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(160))
    exterior: Mapped[str] = mapped_column(String(80), default="")
    category: Mapped[str] = mapped_column(String(80), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    pool_id: Mapped[int | None] = mapped_column(ForeignKey("monitor_pools.id"), nullable=True, index=True)

    snapshots: Mapped[list["MarketSnapshot"]] = relationship(back_populates="item")
    pool: Mapped["MonitorPool | None"] = relationship(back_populates="items")


class MonitorPool(Base):
    __tablename__ = "monitor_pools"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)
    interval_minutes: Mapped[int] = mapped_column(Integer, default=10)
    description: Mapped[str] = mapped_column(String(240), default="")
    last_collected_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    items: Mapped[list[Item]] = relationship(back_populates="pool")


class MarketSnapshot(Base):
    __tablename__ = "market_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"), index=True)
    platform_id: Mapped[int] = mapped_column(ForeignKey("platforms.id"), index=True)
    lowest_price: Mapped[float] = mapped_column(Float)
    sell_count: Mapped[int] = mapped_column(Integer)
    highest_buy_price: Mapped[float] = mapped_column(Float)
    buy_count: Mapped[int] = mapped_column(Integer)
    volume_24h: Mapped[int] = mapped_column(Integer)
    avg_price_24h: Mapped[float] = mapped_column(Float)
    raw_payload: Mapped[str] = mapped_column(Text, default="{}")
    captured_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    item: Mapped[Item] = relationship(back_populates="snapshots")
    platform: Mapped[Platform] = relationship()


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"), index=True)
    platform_id: Mapped[int] = mapped_column(ForeignKey("platforms.id"), index=True)
    snapshot_id: Mapped[int] = mapped_column(ForeignKey("market_snapshots.id"), index=True)
    alert_type: Mapped[str] = mapped_column(String(80), index=True)
    severity: Mapped[str] = mapped_column(String(20), default="P2")
    direction: Mapped[str] = mapped_column(String(80), default="暂不明确")
    title: Mapped[str] = mapped_column(String(240))
    detail: Mapped[str] = mapped_column(Text)
    previous_value: Mapped[float] = mapped_column(Float)
    current_value: Mapped[float] = mapped_column(Float)
    absolute_change: Mapped[float] = mapped_column(Float)
    change_rate: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    item: Mapped[Item] = relationship()
    platform: Mapped[Platform] = relationship()
    snapshot: Mapped[MarketSnapshot] = relationship()


class PushRecord(Base):
    __tablename__ = "push_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    alert_id: Mapped[int] = mapped_column(ForeignKey("alerts.id"), index=True)
    channel: Mapped[str] = mapped_column(String(40), index=True)
    status: Mapped[str] = mapped_column(String(40), default="pending")
    target: Mapped[str] = mapped_column(String(240), default="")
    message: Mapped[str] = mapped_column(Text)
    error: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    alert: Mapped[Alert] = relationship()


class BacktestResult(Base):
    __tablename__ = "backtest_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    alert_id: Mapped[int] = mapped_column(ForeignKey("alerts.id"), index=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"), index=True)
    platform_id: Mapped[int] = mapped_column(ForeignKey("platforms.id"), index=True)
    horizon_minutes: Mapped[int] = mapped_column(Integer, index=True)
    entry_price: Mapped[float] = mapped_column(Float)
    exit_price: Mapped[float] = mapped_column(Float)
    price_change: Mapped[float] = mapped_column(Float)
    change_rate: Mapped[float] = mapped_column(Float)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    alert: Mapped[Alert] = relationship()
    item: Mapped[Item] = relationship()
    platform: Mapped[Platform] = relationship()


class StrategyConfig(Base):
    __tablename__ = "strategy_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)
    min_absolute_sell_change: Mapped[int] = mapped_column(Integer, default=30)
    min_sell_change_rate: Mapped[float] = mapped_column(Float, default=0.12)
    min_price_change_rate: Mapped[float] = mapped_column(Float, default=0.035)
    min_buy_change_rate: Mapped[float] = mapped_column(Float, default=0.12)
    cooldown_minutes: Mapped[int] = mapped_column(Integer, default=20)
