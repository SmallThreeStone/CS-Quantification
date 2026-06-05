from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models import Alert, MarketSnapshot, StrategyConfig


class AlertDetector:
    def __init__(self, db: Session, config: StrategyConfig) -> None:
        self.db = db
        self.config = config

    def detect(self, previous: MarketSnapshot | None, current: MarketSnapshot) -> list[Alert]:
        if previous is None:
            return []
        alerts = []
        alerts.extend(self._sell_count_alert(previous, current))
        alerts.extend(self._buy_count_alert(previous, current))
        alerts.extend(self._price_alert(previous, current))
        return alerts

    def _sell_count_alert(self, previous: MarketSnapshot, current: MarketSnapshot) -> list[Alert]:
        change = current.sell_count - previous.sell_count
        rate = change / max(previous.sell_count, 1)
        if abs(change) < self._min_absolute_sell_change and abs(rate) < self._min_sell_change_rate:
            return []
        direction = "偏卖压风险" if change > 0 and current.lowest_price <= previous.lowest_price else "偏扫货拉升"
        return [
            self._build_alert(
                current,
                "在售变化",
                "P1" if abs(rate) >= 0.18 else "P2",
                direction,
                previous.sell_count,
                current.sell_count,
                change,
                rate,
            )
        ]

    def _buy_count_alert(self, previous: MarketSnapshot, current: MarketSnapshot) -> list[Alert]:
        change = current.buy_count - previous.buy_count
        rate = change / max(previous.buy_count, 1)
        if abs(rate) < self._min_buy_change_rate:
            return []
        direction = "偏买入机会" if change > 0 else "偏流动性异常"
        return [
            self._build_alert(
                current,
                "求购变化",
                "P1" if abs(rate) >= 0.2 else "P2",
                direction,
                previous.buy_count,
                current.buy_count,
                change,
                rate,
            )
        ]

    def _price_alert(self, previous: MarketSnapshot, current: MarketSnapshot) -> list[Alert]:
        change = current.lowest_price - previous.lowest_price
        rate = change / max(previous.lowest_price, 1)
        if abs(rate) < self._min_price_change_rate:
            return []
        direction = "偏扫货拉升" if change > 0 else "偏卖压风险"
        return [
            self._build_alert(
                current,
                "底价变化",
                "P1" if abs(rate) >= 0.06 else "P2",
                direction,
                previous.lowest_price,
                current.lowest_price,
                change,
                rate,
            )
        ]

    def _build_alert(
        self,
        current: MarketSnapshot,
        alert_type: str,
        severity: str,
        direction: str,
        previous_value: float,
        current_value: float,
        absolute_change: float,
        change_rate: float,
    ) -> Alert:
        if self._is_in_cooldown(current.item_id, alert_type):
            return Alert(
                item_id=current.item_id,
                platform_id=current.platform_id,
                snapshot_id=current.id,
                alert_type=alert_type,
                severity="P3",
                direction="重复告警已降级",
                title=f"{current.item.display_name} {alert_type}",
                detail="同类告警仍在冷却期内，仅记录不建议推送。",
                previous_value=previous_value,
                current_value=current_value,
                absolute_change=absolute_change,
                change_rate=change_rate,
            )
        sign = "+" if absolute_change > 0 else ""
        detail = (
            f"{alert_type}: {previous_value:.2f} -> {current_value:.2f} "
            f"({sign}{absolute_change:.2f}, {change_rate * 100:.2f}%)"
        )
        return Alert(
            item_id=current.item_id,
            platform_id=current.platform_id,
            snapshot_id=current.id,
            alert_type=alert_type,
            severity=severity,
            direction=direction,
            title=f"{current.item.display_name} {alert_type}",
            detail=detail,
            previous_value=previous_value,
            current_value=current_value,
            absolute_change=absolute_change,
            change_rate=change_rate,
        )

    def _is_in_cooldown(self, item_id: int, alert_type: str) -> bool:
        since = datetime.utcnow() - timedelta(minutes=self._cooldown_minutes)
        return (
            self.db.query(Alert)
            .filter(Alert.item_id == item_id, Alert.alert_type == alert_type, Alert.created_at >= since)
            .first()
            is not None
        )

    @property
    def _min_absolute_sell_change(self) -> int:
        return self.config.min_absolute_sell_change or 30

    @property
    def _min_sell_change_rate(self) -> float:
        return self.config.min_sell_change_rate or 0.12

    @property
    def _min_buy_change_rate(self) -> float:
        return self.config.min_buy_change_rate or 0.12

    @property
    def _min_price_change_rate(self) -> float:
        return self.config.min_price_change_rate or 0.035

    @property
    def _cooldown_minutes(self) -> int:
        return self.config.cooldown_minutes or 20
