from datetime import datetime, timedelta

from app.models import Item, MonitorPool, Platform, StrategyConfig
from app.services.market_service import MarketService


def test_collect_due_pools_only_collects_due_pool_items(db_session):
    platform = Platform(code="steam", name="Steam")
    due_pool = MonitorPool(name="重点池", interval_minutes=10, last_collected_at=None)
    waiting_pool = MonitorPool(name="观察池", interval_minutes=30, last_collected_at=datetime.utcnow())
    db_session.add_all([platform, due_pool, waiting_pool, StrategyConfig(name="default")])
    db_session.flush()
    db_session.add(Item(market_hash_name="due", display_name="到期", pool_id=due_pool.id, is_active=True))
    db_session.add(Item(market_hash_name="waiting", display_name="未到期", pool_id=waiting_pool.id, is_active=True))
    db_session.commit()

    MarketService(db_session).collect_due_pools()

    assert len(due_pool.items[0].snapshots) == 1
    assert len(waiting_pool.items[0].snapshots) == 0
    assert due_pool.last_collected_at is not None


def test_collect_due_pools_collects_again_after_interval(db_session):
    platform = Platform(code="steam", name="Steam")
    pool = MonitorPool(name="重点池", interval_minutes=10, last_collected_at=datetime.utcnow() - timedelta(minutes=11))
    db_session.add_all([platform, pool, StrategyConfig(name="default")])
    db_session.flush()
    db_session.add(Item(market_hash_name="due-again", display_name="再次到期", pool_id=pool.id, is_active=True))
    db_session.commit()

    MarketService(db_session).collect_due_pools()

    assert len(pool.items[0].snapshots) == 1
