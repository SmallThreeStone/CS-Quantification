from sqlalchemy.orm import Session

from app.models import Item, MonitorPool, Platform, StrategyConfig


def seed_defaults(db: Session) -> None:
    if not db.query(Platform).filter_by(code="steam").first():
        db.add(Platform(code="steam", name="Steam Community Market"))
    if not db.query(MonitorPool).filter_by(name="重点池").first():
        db.add(MonitorPool(name="重点池", interval_minutes=10, description="常倒货饰品"))
    if not db.query(StrategyConfig).filter_by(name="default").first():
        db.add(StrategyConfig(name="default"))
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
                )
            )
    db.commit()
