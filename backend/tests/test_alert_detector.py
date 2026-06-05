from datetime import datetime

from app.models import Alert, Item, MarketSnapshot, Platform, StrategyConfig
from app.services.alert_detector import AlertDetector


def snapshot(item: Item, platform: Platform, price: float, sell: int, buy_price: float, buy: int) -> MarketSnapshot:
    row = MarketSnapshot(
        item_id=item.id,
        platform_id=platform.id,
        lowest_price=price,
        sell_count=sell,
        highest_buy_price=buy_price,
        buy_count=buy,
        volume_24h=10,
        avg_price_24h=price,
        captured_at=datetime.utcnow(),
    )
    row.item = item
    row.platform = platform
    return row


def test_sell_count_jump_creates_sell_pressure_alert(db_session):
    item = Item(id=1, market_hash_name="test", display_name="测试饰品")
    platform = Platform(id=1, code="steam", name="Steam")
    config = StrategyConfig(name="default", min_absolute_sell_change=30, min_sell_change_rate=0.12)
    previous = snapshot(item, platform, 100, 200, 95, 30)
    current = snapshot(item, platform, 95, 250, 92, 28)

    alerts = AlertDetector(db_session, config).detect(previous, current)

    assert alerts[0].alert_type == "在售变化"
    assert alerts[0].direction == "偏卖压风险"
    assert alerts[0].absolute_change == 50


def test_price_drop_creates_price_alert(db_session):
    item = Item(id=1, market_hash_name="test", display_name="测试饰品")
    platform = Platform(id=1, code="steam", name="Steam")
    config = StrategyConfig(name="default", min_price_change_rate=0.035)
    previous = snapshot(item, platform, 100, 20, 95, 30)
    current = snapshot(item, platform, 94, 22, 90, 30)

    alerts = AlertDetector(db_session, config).detect(previous, current)

    assert any(alert.alert_type == "底价变化" for alert in alerts)


def test_cooldown_downgrades_duplicate_alert(db_session):
    item = Item(id=1, market_hash_name="test", display_name="测试饰品")
    platform = Platform(id=1, code="steam", name="Steam")
    config = StrategyConfig(name="default", min_absolute_sell_change=30, min_sell_change_rate=0.12)
    previous = snapshot(item, platform, 100, 100, 95, 30)
    current = snapshot(item, platform, 98, 140, 94, 30)
    db_session.add(
        Alert(
            item_id=1,
            platform_id=1,
            snapshot_id=1,
            alert_type="在售变化",
            severity="P1",
            direction="偏卖压风险",
            title="测试",
            detail="测试",
            previous_value=100,
            current_value=140,
            absolute_change=40,
            change_rate=0.4,
        )
    )
    db_session.commit()

    alerts = AlertDetector(db_session, config).detect(previous, current)

    assert alerts[0].severity == "P3"
