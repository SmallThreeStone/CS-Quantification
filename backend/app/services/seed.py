from sqlalchemy.orm import Session

from app.models import Item, MonitorPool, Platform, StrategyConfig


def seed_defaults(db: Session) -> None:
    if not db.query(Platform).filter_by(code="steam").first():
        db.add(Platform(code="steam", name="Steam Community Market"))
    pools = [
        ("重点池", 10, "常倒货饰品"),
        ("观察池", 30, "热门饰品、箱子、贴纸"),
        ("事件池", 5, "版本更新、Major、贴纸打折期间临时监控"),
    ]
    for name, interval_minutes, description in pools:
        if not db.query(MonitorPool).filter_by(name=name).first():
            db.add(MonitorPool(name=name, interval_minutes=interval_minutes, description=description))
    if not db.query(StrategyConfig).filter_by(name="default").first():
        db.add(StrategyConfig(name="default"))
    db.flush()
    default_pool = db.query(MonitorPool).filter_by(name="重点池").one()
    items = [
        ("★ Specialist Gloves | Emerald Web (Field-Tested)", "超导体", "略有磨损/久经沙场", "gloves"),
        ("★ Sport Gloves | Vice (Field-Tested)", "清凉薄荷", "略有磨损/久经沙场", "gloves"),
    ]
    for market_hash_name, display_name, exterior, category in items:
        if not db.query(Item).filter_by(market_hash_name=market_hash_name).first():
            db.add(
                Item(
                    market_hash_name=market_hash_name,
                    display_name=display_name,
                    exterior=exterior,
                    category=category,
                    is_active=True,
                    pool_id=default_pool.id,
                )
            )
        else:
            item = db.query(Item).filter_by(market_hash_name=market_hash_name).one()
            if item.pool_id is None:
                item.pool_id = default_pool.id
    db.commit()
