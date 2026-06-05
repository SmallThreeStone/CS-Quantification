from datetime import datetime

from app.models import Alert, Item, MarketSnapshot, Platform
from app.services.push_service import PushService


def test_dispatch_without_webhook_records_skipped_push(db_session):
    item, platform, alert = create_alert(db_session)

    records = PushService(db_session).dispatch_alerts([alert])

    assert len(records) == 1
    assert records[0].status == "skipped"
    assert records[0].alert_id == alert.id
    assert "未配置推送 Webhook" in records[0].error
    assert item.display_name in records[0].message
    assert platform.name not in records[0].message


def test_push_message_contains_decision_fields(db_session):
    _, _, alert = create_alert(db_session)

    message = PushService(db_session)._message(alert)

    assert "时间:" in message
    assert "饰品:" in message
    assert "类型:" in message
    assert "详情:" in message
    assert "系统判断:" in message
    assert "历史告警简报" in message
    assert "在售：" in message
    assert "求购：" in message
    assert "底价：" in message
    assert "波动：" in message
    assert "成交：" in message


def test_push_message_groups_recent_history(db_session):
    _, platform, alert = create_alert(db_session)
    db_session.add_all(
        [
            history_alert(alert, platform, "在售变化", 328, 259, -69, datetime(2026, 6, 5, 9, 41)),
            history_alert(alert, platform, "在售变化", 305, 375, 70, datetime(2026, 6, 4, 19, 35)),
            history_alert(alert, platform, "在售变化", 376, 305, -71, datetime(2026, 6, 4, 19, 10)),
            history_alert(alert, platform, "在售变化", 300, 320, 20, datetime(2026, 6, 4, 18, 10)),
            history_alert(alert, platform, "求购变化", 106, 88, -18, datetime(2026, 6, 4, 13, 55)),
            history_alert(alert, platform, "底价变化", 294.5, 282, -12.5, datetime(2026, 6, 5, 10, 7)),
            history_alert(alert, platform, "价格波动异常", 300, 282, -18, datetime(2026, 6, 5, 10, 6)),
            history_alert(alert, platform, "成交量异常", 20, 45, 25, datetime(2026, 6, 5, 10, 8)),
        ]
    )
    db_session.commit()

    message = PushService(db_session)._message(alert)

    assert "在售：\n06-05 09:41 328.00->259.00 (-69.00)" in message
    assert "06-04 18:10" not in message
    assert "求购：\n06-04 13:55 106.00->88.00 (-18.00)" in message
    assert "底价：\n06-05 10:07 294.50->282.00 (-12.50)" in message
    assert "波动：\n06-05 10:06 300.00->282.00 (-18.00)" in message
    assert "成交：\n06-05 10:08 20.00->45.00 (+25.00)" in message
    assert "259.00->310.00" not in message


def create_alert(db_session):
    item = Item(market_hash_name="test", display_name="测试饰品", exterior="崭新出厂", category="rifle")
    platform = Platform(code="steam", name="Steam")
    db_session.add_all([item, platform])
    db_session.flush()
    snapshot = MarketSnapshot(
        item_id=item.id,
        platform_id=platform.id,
        lowest_price=282,
        sell_count=310,
        highest_buy_price=260,
        buy_count=88,
        volume_24h=20,
        avg_price_24h=294,
        captured_at=datetime.utcnow(),
    )
    db_session.add(snapshot)
    db_session.flush()
    alert = Alert(
        item_id=item.id,
        platform_id=platform.id,
        snapshot_id=snapshot.id,
        alert_type="在售变化",
        severity="P1",
        direction="偏卖压风险",
        title="测试饰品 在售变化",
        detail="在售变化: 259.00 -> 310.00 (+51.00, 19.69%)",
        previous_value=259,
        current_value=310,
        absolute_change=51,
        change_rate=0.1969,
    )
    db_session.add(alert)
    db_session.commit()
    return item, platform, alert


def history_alert(
    source: Alert,
    platform: Platform,
    alert_type: str,
    previous_value: float,
    current_value: float,
    absolute_change: float,
    created_at: datetime,
) -> Alert:
    return Alert(
        item_id=source.item_id,
        platform_id=platform.id,
        snapshot_id=source.snapshot_id,
        alert_type=alert_type,
        severity="P2",
        direction="历史",
        title=f"测试饰品 {alert_type}",
        detail=f"{alert_type}: {previous_value:.2f} -> {current_value:.2f}",
        previous_value=previous_value,
        current_value=current_value,
        absolute_change=absolute_change,
        change_rate=absolute_change / max(previous_value, 1),
        created_at=created_at,
    )
