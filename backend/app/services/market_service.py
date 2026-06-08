import json
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.config import settings
from app.models import Alert, CollectRunLog, Item, MarketSnapshot, MonitorPool, Platform, StrategyConfig
from app.services.alert_detector import AlertDetector
from app.services.market_provider import get_market_provider


class MarketService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.provider = get_market_provider()
        self.last_run_log: CollectRunLog | None = None

    def collect_active_items(self) -> list[Alert]:
        return self._collect_items(self.db.query(Item).filter_by(is_active=True).all(), mode="manual")

    def collect_due_pools(self) -> list[Alert]:
        due_items: list[Item] = []
        now = datetime.utcnow()
        pools = self.db.query(MonitorPool).all()
        for pool in pools:
            if self._pool_due(pool, now):
                due_items.extend([item for item in pool.items if item.is_active])
                pool.last_collected_at = now
        alerts = self._collect_items(due_items, mode="worker")
        return alerts

    def push_suppress_reason(self) -> str:
        log = self.last_run_log
        if log is None or log.snapshot_count == 0:
            return ""
        total_fields = log.real_field_count + log.fallback_field_count
        real_ratio = log.real_field_count / total_fields if total_fields else 0
        fallback_item_ratio = log.fallback_count / max(log.snapshot_count, 1)
        if log.real_field_count == 0:
            return "数据源异常：本轮采集无真实字段，跳过外部推送"
        if real_ratio < 0.3:
            return f"数据源异常：真实字段占比 {real_ratio * 100:.1f}% 偏低，跳过外部推送"
        if log.snapshot_count >= 3 and fallback_item_ratio >= 0.8:
            return f"数据源异常：fallback 覆盖 {fallback_item_ratio * 100:.1f}% 饰品，跳过外部推送"
        return ""

    def _collect_items(self, items: list[Item], mode: str) -> list[Alert]:
        running = self.db.query(CollectRunLog).filter_by(status="running").first()
        if running is not None:
            self.last_run_log = running
            return []
        if settings.collect_item_limit > 0:
            items = items[: settings.collect_item_limit]
        started = datetime.utcnow()
        log = CollectRunLog(mode=mode, provider=settings.market_provider, item_count=len(items), started_at=started)
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        self.last_run_log = log
        platform = self.db.query(Platform).filter_by(code="steam").one()
        config = self.db.query(StrategyConfig).filter_by(name="default").one()
        alerts: list[Alert] = []
        snapshots = 0
        real_fields = 0
        fallback_fields = 0
        fallback_count = 0
        errors: list[str] = []
        seen: set[int] = set()
        for item in items:
            if item.id in seen:
                continue
            seen.add(item.id)
            try:
                previous = self._latest_snapshot(item.id, platform.id)
                quote = self.provider.fetch_quote(item.market_hash_name, item.steam_item_nameid)
                quality = quote.raw_payload.get("source_quality", {})
                real_fields += len(quality.get("real_fields", []))
                fallback_fields += len(quality.get("fallback_fields", []))
                fallback_count += 1 if quality.get("is_fallback") or quality.get("fallback_fields") else 0
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
                snapshots += 1
                snapshot.item = item
                snapshot.platform = platform
                detected = AlertDetector(self.db, config).detect(previous, snapshot)
                for alert in detected:
                    self.db.add(alert)
                alerts.extend(detected)
                self.db.commit()
            except Exception as exc:
                errors.append(f"{item.display_name}: {exc}")
                self.db.rollback()
        finished = datetime.utcnow()
        log = self.db.get(CollectRunLog, log.id)
        if log is None:
            return alerts
        log.status = "failed" if snapshots == 0 and errors else "partial" if errors else "success"
        log.snapshot_count = snapshots
        log.alert_count = len(alerts)
        log.error_count = len(errors)
        log.real_field_count = real_fields
        log.fallback_field_count = fallback_fields
        log.fallback_count = fallback_count
        log.error = "\n".join(errors[:10])
        log.finished_at = finished
        log.duration_ms = int((finished - started).total_seconds() * 1000)
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
