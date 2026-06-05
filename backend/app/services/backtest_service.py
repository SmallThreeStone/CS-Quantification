from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models import Alert, BacktestResult, MarketSnapshot


HORIZONS = [10, 30, 60, 360, 1440]


class BacktestService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def evaluate_due_alerts(self, now: datetime | None = None) -> list[BacktestResult]:
        now = now or datetime.utcnow()
        results: list[BacktestResult] = []
        alerts = self.db.query(Alert).order_by(Alert.created_at.asc()).all()
        for alert in alerts:
            for horizon in HORIZONS:
                if alert.created_at + timedelta(minutes=horizon) > now:
                    continue
                if self._has_result(alert.id, horizon):
                    continue
                exit_snapshot = self._exit_snapshot(alert, horizon)
                if exit_snapshot is None:
                    continue
                entry_price = alert.snapshot.lowest_price
                exit_price = exit_snapshot.lowest_price
                change = exit_price - entry_price
                result = BacktestResult(
                    alert_id=alert.id,
                    item_id=alert.item_id,
                    platform_id=alert.platform_id,
                    horizon_minutes=horizon,
                    entry_price=entry_price,
                    exit_price=exit_price,
                    price_change=change,
                    change_rate=change / max(entry_price, 1),
                    evaluated_at=exit_snapshot.captured_at,
                )
                self.db.add(result)
                results.append(result)
        self.db.commit()
        return results

    def summary(self) -> list[dict]:
        rows = self.db.query(BacktestResult).all()
        buckets: dict[tuple[str, int], list[BacktestResult]] = {}
        for row in rows:
            buckets.setdefault((row.alert.alert_type, row.horizon_minutes), []).append(row)
        summary = []
        for (alert_type, horizon), results in sorted(buckets.items(), key=lambda item: (item[0][0], item[0][1])):
            wins = sum(1 for result in results if self._is_win(result))
            avg_change = sum(result.change_rate for result in results) / len(results)
            max_gain = max(result.change_rate for result in results)
            max_drawdown = min(result.change_rate for result in results)
            summary.append(
                {
                    "alert_type": alert_type,
                    "horizon_minutes": horizon,
                    "sample_count": len(results),
                    "win_count": wins,
                    "win_rate": wins / len(results),
                    "avg_change_rate": avg_change,
                    "max_gain_rate": max_gain,
                    "max_drawdown_rate": max_drawdown,
                    "profit_loss_ratio": self._profit_loss_ratio(results),
                    "confidence_level": self._confidence_level(len(results)),
                }
            )
        return summary

    def _has_result(self, alert_id: int, horizon: int) -> bool:
        return (
            self.db.query(BacktestResult)
            .filter(BacktestResult.alert_id == alert_id, BacktestResult.horizon_minutes == horizon)
            .first()
            is not None
        )

    def _exit_snapshot(self, alert: Alert, horizon: int) -> MarketSnapshot | None:
        target = alert.created_at + timedelta(minutes=horizon)
        return (
            self.db.query(MarketSnapshot)
            .filter(
                MarketSnapshot.item_id == alert.item_id,
                MarketSnapshot.platform_id == alert.platform_id,
                MarketSnapshot.captured_at >= target,
            )
            .order_by(MarketSnapshot.captured_at.asc())
            .first()
        )

    def _is_win(self, result: BacktestResult) -> bool:
        direction = result.alert.direction
        if direction in ("偏买入机会", "偏扫货拉升"):
            return result.price_change > 0
        if direction == "偏卖压风险":
            return result.price_change < 0
        return False

    def _profit_loss_ratio(self, results: list[BacktestResult]) -> float:
        gains = [result.change_rate for result in results if result.change_rate > 0]
        losses = [abs(result.change_rate) for result in results if result.change_rate < 0]
        if not gains or not losses:
            return 0
        return (sum(gains) / len(gains)) / (sum(losses) / len(losses))

    def _confidence_level(self, sample_count: int) -> str:
        if sample_count >= 30:
            return "高"
        if sample_count >= 10:
            return "中"
        return "低"
