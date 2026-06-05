from datetime import datetime, timedelta

import pytest

from app.models import Alert, Item, MarketSnapshot, Platform
from app.services.backtest_service import BacktestService


def test_backtest_evaluates_due_alert_with_later_snapshot(db_session):
    alert = create_alert_with_snapshots(db_session, direction="偏买入机会", exit_price=120)

    results = BacktestService(db_session).evaluate_due_alerts(now=alert.created_at + timedelta(minutes=11))
    duplicate = BacktestService(db_session).evaluate_due_alerts(now=alert.created_at + timedelta(minutes=11))

    assert len(results) == 1
    assert results[0].horizon_minutes == 10
    assert results[0].price_change == 20
    assert len(duplicate) == 0


def test_backtest_summary_counts_directional_win(db_session):
    alert = create_alert_with_snapshots(db_session, direction="偏卖压风险", exit_price=90)
    BacktestService(db_session).evaluate_due_alerts(now=alert.created_at + timedelta(minutes=11))

    summary = BacktestService(db_session).summary()

    assert summary[0]["alert_type"] == "底价变化"
    assert summary[0]["sample_count"] == 1
    assert summary[0]["win_count"] == 1
    assert summary[0]["win_rate"] == 1
    assert summary[0]["max_gain_rate"] == pytest.approx(-0.1)
    assert summary[0]["max_drawdown_rate"] == pytest.approx(-0.1)
    assert summary[0]["profit_loss_ratio"] == 0
    assert summary[0]["confidence_level"] == "低"


def test_backtest_summary_tracks_extremes_and_profit_loss_ratio(db_session):
    winning_alert = create_alert_with_snapshots(db_session, direction="偏买入机会", exit_price=120, suffix="win")
    losing_alert = create_alert_with_snapshots(db_session, direction="偏买入机会", exit_price=90, suffix="loss")
    BacktestService(db_session).evaluate_due_alerts(now=winning_alert.created_at + timedelta(minutes=11))
    BacktestService(db_session).evaluate_due_alerts(now=losing_alert.created_at + timedelta(minutes=11))

    summary = BacktestService(db_session).summary()

    assert len(summary) == 1
    assert summary[0]["sample_count"] == 2
    assert summary[0]["win_count"] == 1
    assert summary[0]["avg_change_rate"] == pytest.approx(0.05)
    assert summary[0]["max_gain_rate"] == pytest.approx(0.2)
    assert summary[0]["max_drawdown_rate"] == pytest.approx(-0.1)
    assert summary[0]["profit_loss_ratio"] == pytest.approx(2)


def create_alert_with_snapshots(db_session, direction: str, exit_price: float, suffix: str = "") -> Alert:
    key = f"{direction}-{suffix}" if suffix else direction
    item = Item(market_hash_name=f"item-{key}", display_name="测试饰品")
    platform = Platform(code=f"steam-{key}", name="Steam")
    db_session.add_all([item, platform])
    db_session.flush()
    created_at = datetime.utcnow() - timedelta(minutes=20)
    entry = MarketSnapshot(
        item_id=item.id,
        platform_id=platform.id,
        lowest_price=100,
        sell_count=20,
        highest_buy_price=95,
        buy_count=10,
        volume_24h=5,
        avg_price_24h=100,
        captured_at=created_at,
    )
    exit_snapshot = MarketSnapshot(
        item_id=item.id,
        platform_id=platform.id,
        lowest_price=exit_price,
        sell_count=20,
        highest_buy_price=95,
        buy_count=10,
        volume_24h=5,
        avg_price_24h=exit_price,
        captured_at=created_at + timedelta(minutes=10),
    )
    db_session.add_all([entry, exit_snapshot])
    db_session.flush()
    alert = Alert(
        item_id=item.id,
        platform_id=platform.id,
        snapshot_id=entry.id,
        alert_type="底价变化",
        severity="P1",
        direction=direction,
        title="测试",
        detail="测试",
        previous_value=100,
        current_value=100,
        absolute_change=0,
        change_rate=0,
        created_at=created_at,
    )
    db_session.add(alert)
    db_session.commit()
    return alert
