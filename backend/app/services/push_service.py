from datetime import datetime

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Alert, PushRecord


class PushService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def dispatch_alerts(self, alerts: list[Alert]) -> list[PushRecord]:
        records = []
        for alert in alerts:
            if alert.severity == "P3":
                records.append(self._record(alert, "none", "skipped", "", self._message(alert), "P3 告警不推送"))
                continue
            channel, webhook = self._target()
            message = self._message(alert)
            if not webhook:
                records.append(self._record(alert, channel, "skipped", "", message, "未配置推送 Webhook"))
                continue
            records.append(self._send(alert, channel, webhook, message))
        self.db.commit()
        return records

    def _send(self, alert: Alert, channel: str, webhook: str, message: str) -> PushRecord:
        record = self._record(alert, channel, "pending", webhook, message, "")
        try:
            payload = self._payload(channel, message)
            response = httpx.post(webhook, json=payload, timeout=8)
            response.raise_for_status()
            record.status = "sent"
            record.sent_at = datetime.utcnow()
        except Exception as exc:
            record.status = "failed"
            record.error = str(exc)
        return record

    def _record(
        self,
        alert: Alert,
        channel: str,
        status: str,
        target: str,
        message: str,
        error: str,
    ) -> PushRecord:
        record = PushRecord(
            alert_id=alert.id,
            channel=channel,
            status=status,
            target=target,
            message=message,
            error=error,
        )
        self.db.add(record)
        self.db.flush()
        return record

    def _target(self) -> tuple[str, str]:
        channel = settings.push_channel.lower()
        if channel == "wechat":
            return "wechat", settings.wechat_webhook_url
        if channel == "qq":
            return "qq", settings.qq_webhook_url
        if settings.wechat_webhook_url:
            return "wechat", settings.wechat_webhook_url
        if settings.qq_webhook_url:
            return "qq", settings.qq_webhook_url
        return channel or "none", ""

    def _payload(self, channel: str, message: str) -> dict:
        if channel == "wechat":
            return {"msgtype": "text", "text": {"content": message}}
        return {"msg_type": "text", "content": {"text": message}}

    def _message(self, alert: Alert) -> str:
        history = self._history(alert)
        snapshot = alert.snapshot
        lines = [
            f"时间: {alert.created_at:%Y-%m-%d %H:%M:%S}",
            f"饰品: {alert.item.display_name} ({alert.item.exterior})",
            f"类型: {alert.alert_type}",
            "详情:",
            f"· {alert.detail}",
            (
                f"  底价: ¥{snapshot.lowest_price:.2f}  在售: {snapshot.sell_count}  "
                f"最高求购: ¥{snapshot.highest_buy_price:.2f}  求购: {snapshot.buy_count}"
            ),
            f"系统判断: {alert.direction}",
            "历史告警简报（近3次）:",
        ]
        if history:
            lines.extend(history)
        else:
            lines.append("暂无同类历史告警")
        return "\n".join(lines)

    def _history(self, alert: Alert) -> list[str]:
        rows = (
            self.db.query(Alert)
            .filter(Alert.item_id == alert.item_id, Alert.alert_type == alert.alert_type, Alert.id != alert.id)
            .order_by(Alert.created_at.desc())
            .limit(3)
            .all()
        )
        return [
            f"{row.created_at:%m-%d %H:%M} {row.previous_value:.2f}->{row.current_value:.2f} ({row.absolute_change:+.2f})"
            for row in rows
        ]
