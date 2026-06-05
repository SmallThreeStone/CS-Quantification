import json
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models import Alert, Item, MarketSnapshot, MonitorPool, Platform, StrategyConfig
from app.services.alert_detector import AlertDetector
from app.services.market_provider import get_market_provider


class MarketService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.provider = get_market_provider()

    def collect_active_items(self) -> list[Alert]:
        return self._collect_items(self.db.query(Item).filter_by(is_active=True).all(), mark_pools=False)

    def collect_due_pools(self) -> list[Alert]:
        due_items: list[Item] = []
        now = datetime.utcnow()
        pools = self.db.query(MonitorPool).all()
        for pool in pools:
            if self._pool_due(pool, now):
                due_items.extend([item for item in pool.items if item.is_active])
                pool.last_collected_at = now
        alerts = self._collect_items(due_items, mark_pools=True)
        return alerts

    def _collect_items(self, items: list[Item], mark_pools: bool) -> list[Alert]:
        platform = self.db.query(Platform).filter_by(code="steam").one()
        config = self.db.query(StrategyConfig).filter_by(name="default").one()
        alerts: list[Alert] = []
        seen: set[int] = set()
        for item in items:
            if item.id in seen:
                continue
            seen.add(item.id)
            previous = self._latest_snapshot(item.id, platform.id)
            quote = self.provider.fetch_quote(item.market_hash_name)
            snapshot = MarketSnapshot(
                item_id=item.id,
                platform_id=platform.id,
                lowest_price=quote.lowest_price,
                sell_count=quote.sell_count,
                highest_buy_price=quote.highest_buy_price,
                buy_count=quote.buy_count,
                volume_24h=quote.volume_24h,
                avg_price_24h=quote.avg_price_24h,
                raw_payload=json.dumps(quote.raw_payload, ensure_ascii=False),
                captured_at=quote.captured_at,
            )
            self.db.add(snapshot)
            self.db.flush()
            snapshot.item = item
            snapshot.platform = platform
            detected = AlertDetector(self.db, config).detect(previous, snapshot)
            for alert in detected:
                self.db.add(alert)
            alerts.extend(detected)
        self.db.commit()
        return alerts

    def _pool_due(self, pool: MonitorPool, now: datetime) -> bool:
        if pool.last_collected_at is None:
            return True
        return pool.last_collected_at <= now - timedelta(minutes=pool.interval_minutes)

    def _latest_snapshot(self, item_id: int, platform_id: int) -> MarketSnapshot | None:
        return (
            self.db.query(MarketSnapshot)
            .filter(MarketSnapshot.item_id == item_id, MarketSnapshot.platform_id == platform_id)
            .order_by(MarketSnapshot.captured_at.desc())
            .first()
        )
