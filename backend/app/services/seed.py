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
    pool_by_name = {pool.name: pool for pool in db.query(MonitorPool).all()}
    items = [
        ("★ Specialist Gloves | Emerald Web (Field-Tested)", "超导体", "略有磨损/久经沙场", "gloves", "重点池"),
        ("★ Sport Gloves | Vice (Field-Tested)", "清凉薄荷", "略有磨损/久经沙场", "gloves", "重点池"),
        ("AK-47 | Redline (Field-Tested)", "AK-47 | 红线", "久经沙场", "rifle", "观察池"),
        ("AK-47 | The Empress (Field-Tested)", "AK-47 | 皇后", "久经沙场", "rifle", "观察池"),
        ("AK-47 | Asiimov (Field-Tested)", "AK-47 | 二西莫夫", "久经沙场", "rifle", "观察池"),
        ("AK-47 | Slate (Factory New)", "AK-47 | 墨岩", "崭新出厂", "rifle", "观察池"),
        ("M4A1-S | Printstream (Field-Tested)", "M4A1-S | 印花集", "久经沙场", "rifle", "观察池"),
        ("M4A1-S | Hyper Beast (Field-Tested)", "M4A1-S | 暴怒野兽", "久经沙场", "rifle", "观察池"),
        ("M4A4 | Asiimov (Field-Tested)", "M4A4 | 二西莫夫", "久经沙场", "rifle", "观察池"),
        ("AWP | Asiimov (Field-Tested)", "AWP | 二西莫夫", "久经沙场", "sniper", "观察池"),
        ("AWP | Neo-Noir (Field-Tested)", "AWP | 黑色魅影", "久经沙场", "sniper", "观察池"),
        ("AWP | Redline (Field-Tested)", "AWP | 红线", "久经沙场", "sniper", "观察池"),
        ("Desert Eagle | Printstream (Field-Tested)", "沙漠之鹰 | 印花集", "久经沙场", "pistol", "观察池"),
        ("Desert Eagle | Code Red (Field-Tested)", "沙漠之鹰 | 红色代号", "久经沙场", "pistol", "观察池"),
        ("USP-S | Kill Confirmed (Field-Tested)", "USP 消音版 | 枪响人亡", "久经沙场", "pistol", "观察池"),
        ("USP-S | Printstream (Field-Tested)", "USP 消音版 | 印花集", "久经沙场", "pistol", "观察池"),
        ("Glock-18 | Water Elemental (Field-Tested)", "格洛克-18 | 水灵", "久经沙场", "pistol", "观察池"),
        ("★ Driver Gloves | King Snake (Field-Tested)", "驾驶手套 | 王蛇", "久经沙场", "gloves", "观察池"),
        ("★ Sport Gloves | Amphibious (Field-Tested)", "运动手套 | 双栖", "久经沙场", "gloves", "观察池"),
        ("★ Specialist Gloves | Fade (Field-Tested)", "专业手套 | 渐变之色", "久经沙场", "gloves", "观察池"),
        ("★ Hand Wraps | Cobalt Skulls (Field-Tested)", "裹手 | 钴蓝骷髅", "久经沙场", "gloves", "观察池"),
        ("★ Butterfly Knife | Doppler (Factory New)", "蝴蝶刀 | 多普勒", "崭新出厂", "knife", "观察池"),
        ("★ Karambit | Doppler (Factory New)", "爪子刀 | 多普勒", "崭新出厂", "knife", "观察池"),
        ("★ M9 Bayonet | Doppler (Factory New)", "M9 刺刀 | 多普勒", "崭新出厂", "knife", "观察池"),
        ("★ Bayonet | Gamma Doppler (Factory New)", "刺刀 | 伽玛多普勒", "崭新出厂", "knife", "观察池"),
        ("Revolution Case", "变革武器箱", "", "case", "观察池"),
        ("Fracture Case", "裂空武器箱", "", "case", "观察池"),
        ("Snakebite Case", "蛇噬武器箱", "", "case", "观察池"),
        ("Sticker | Natus Vincere | Paris 2023", "NAVI | Paris 2023 贴纸", "", "sticker", "观察池"),
        ("Sticker | G2 Esports | Paris 2023", "G2 | Paris 2023 贴纸", "", "sticker", "观察池"),
    ]
    for market_hash_name, display_name, exterior, category, pool_name in items:
        pool = pool_by_name[pool_name]
        if not db.query(Item).filter_by(market_hash_name=market_hash_name).first():
            db.add(
                Item(
                    market_hash_name=market_hash_name,
                    display_name=display_name,
                    exterior=exterior,
                    category=category,
                    steam_item_nameid="",
                    is_active=True,
                    pool_id=pool.id,
                )
            )
        else:
            item = db.query(Item).filter_by(market_hash_name=market_hash_name).one()
            if item.pool_id is None:
                item.pool_id = pool.id
    db.commit()
