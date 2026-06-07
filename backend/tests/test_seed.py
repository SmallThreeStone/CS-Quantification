from app.models import Item, MonitorPool, Platform, StrategyConfig
from app.services.seed import seed_defaults


def test_seed_defaults_creates_one_hundred_test_items(db_session):
    seed_defaults(db_session)

    items = db_session.query(Item).all()
    pools = {pool.name: pool for pool in db_session.query(MonitorPool).all()}

    assert db_session.query(Platform).filter_by(code="steam").count() == 1
    assert db_session.query(StrategyConfig).filter_by(name="default").count() == 1
    assert len(items) == 100
    assert db_session.query(Item).filter(Item.is_active.is_(True)).count() == 100
    assert db_session.query(Item).filter_by(display_name="超导体", pool_id=pools["重点池"].id).count() == 1
    assert db_session.query(Item).filter_by(display_name="清凉薄荷", pool_id=pools["重点池"].id).count() == 1
    assert db_session.query(Item).filter(Item.pool_id == pools["观察池"].id).count() == 98
