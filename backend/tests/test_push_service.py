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
