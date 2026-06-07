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
        ("AK-47 | Fire Serpent (Field-Tested)", "AK-47 | 火蛇", "久经沙场", "rifle", "观察池"),
        ("AK-47 | Vulcan (Field-Tested)", "AK-47 | 火神", "久经沙场", "rifle", "观察池"),
        ("AK-47 | Bloodsport (Field-Tested)", "AK-47 | 血腥运动", "久经沙场", "rifle", "观察池"),
        ("AK-47 | Neon Rider (Field-Tested)", "AK-47 | 霓虹骑士", "久经沙场", "rifle", "观察池"),
        ("AK-47 | Case Hardened (Field-Tested)", "AK-47 | 表面淬火", "久经沙场", "rifle", "观察池"),
        ("M4A1-S | Golden Coil (Field-Tested)", "M4A1-S | 金蛇缠绕", "久经沙场", "rifle", "观察池"),
        ("M4A1-S | Mecha Industries (Field-Tested)", "M4A1-S | 机械工业", "久经沙场", "rifle", "观察池"),
        ("M4A1-S | Player Two (Field-Tested)", "M4A1-S | 二号玩家", "久经沙场", "rifle", "观察池"),
        ("M4A1-S | Decimator (Field-Tested)", "M4A1-S | 暴怒中士", "久经沙场", "rifle", "观察池"),
        ("M4A4 | The Emperor (Field-Tested)", "M4A4 | 皇帝", "久经沙场", "rifle", "观察池"),
        ("M4A4 | In Living Color (Field-Tested)", "M4A4 | 活色生香", "久经沙场", "rifle", "观察池"),
        ("M4A4 | Desolate Space (Field-Tested)", "M4A4 | 死寂空间", "久经沙场", "rifle", "观察池"),
        ("AWP | Wildfire (Field-Tested)", "AWP | 野火", "久经沙场", "sniper", "观察池"),
        ("AWP | Hyper Beast (Field-Tested)", "AWP | 暴怒野兽", "久经沙场", "sniper", "观察池"),
        ("AWP | Containment Breach (Field-Tested)", "AWP | 密林瘟疫", "久经沙场", "sniper", "观察池"),
        ("AWP | Chromatic Aberration (Field-Tested)", "AWP | 色差", "久经沙场", "sniper", "观察池"),
        ("AWP | Duality (Field-Tested)", "AWP | 二元性", "久经沙场", "sniper", "观察池"),
        ("Desert Eagle | Blaze (Factory New)", "沙漠之鹰 | 炽烈之炎", "崭新出厂", "pistol", "观察池"),
        ("Desert Eagle | Ocean Drive (Field-Tested)", "沙漠之鹰 | 海洋大道", "久经沙场", "pistol", "观察池"),
        ("Desert Eagle | Mecha Industries (Field-Tested)", "沙漠之鹰 | 机械工业", "久经沙场", "pistol", "观察池"),
        ("USP-S | The Traitor (Field-Tested)", "USP 消音版 | 叛徒", "久经沙场", "pistol", "观察池"),
        ("USP-S | Neo-Noir (Field-Tested)", "USP 消音版 | 黑色魅影", "久经沙场", "pistol", "观察池"),
        ("Glock-18 | Bullet Queen (Field-Tested)", "格洛克-18 | 子弹皇后", "久经沙场", "pistol", "观察池"),
        ("Glock-18 | Vogue (Field-Tested)", "格洛克-18 | 时尚", "久经沙场", "pistol", "观察池"),
        ("P250 | See Ya Later (Field-Tested)", "P250 | 生化短吻鳄", "久经沙场", "pistol", "观察池"),
        ("FAMAS | Commemoration (Field-Tested)", "法玛斯 | 纪念碑", "久经沙场", "rifle", "观察池"),
        ("Galil AR | Chatterbox (Field-Tested)", "加利尔 AR | 喧闹骷髅", "久经沙场", "rifle", "观察池"),
        ("SSG 08 | Dragonfire (Field-Tested)", "SSG 08 | 鬼火", "久经沙场", "sniper", "观察池"),
        ("MP9 | Starlight Protector (Field-Tested)", "MP9 | 星光守护者", "久经沙场", "smg", "观察池"),
        ("MAC-10 | Stalker (Field-Tested)", "MAC-10 | 追踪者", "久经沙场", "smg", "观察池"),
        ("★ Driver Gloves | Imperial Plaid (Field-Tested)", "驾驶手套 | 紫蓝格子", "久经沙场", "gloves", "观察池"),
        ("★ Driver Gloves | Overtake (Field-Tested)", "驾驶手套 | 超越", "久经沙场", "gloves", "观察池"),
        ("★ Moto Gloves | Polygon (Field-Tested)", "摩托手套 | 多边形", "久经沙场", "gloves", "观察池"),
        ("★ Moto Gloves | Spearmint (Field-Tested)", "摩托手套 | 薄荷", "久经沙场", "gloves", "观察池"),
        ("★ Sport Gloves | Omega (Field-Tested)", "运动手套 | 欧米伽", "久经沙场", "gloves", "观察池"),
        ("★ Sport Gloves | Scarlet Shamagh (Field-Tested)", "运动手套 | 猩红头巾", "久经沙场", "gloves", "观察池"),
        ("★ Specialist Gloves | Crimson Kimono (Field-Tested)", "专业手套 | 深红和服", "久经沙场", "gloves", "观察池"),
        ("★ Specialist Gloves | Mogul (Field-Tested)", "专业手套 | 大腕", "久经沙场", "gloves", "观察池"),
        ("★ Hand Wraps | Slaughter (Field-Tested)", "裹手 | 屠夫", "久经沙场", "gloves", "观察池"),
        ("★ Hand Wraps | CAUTION! (Field-Tested)", "裹手 | 警告", "久经沙场", "gloves", "观察池"),
        ("★ Karambit | Gamma Doppler (Factory New)", "爪子刀 | 伽玛多普勒", "崭新出厂", "knife", "观察池"),
        ("★ Butterfly Knife | Tiger Tooth (Factory New)", "蝴蝶刀 | 虎牙", "崭新出厂", "knife", "观察池"),
        ("★ Butterfly Knife | Slaughter (Factory New)", "蝴蝶刀 | 屠夫", "崭新出厂", "knife", "观察池"),
        ("★ Karambit | Lore (Field-Tested)", "爪子刀 | 传说", "久经沙场", "knife", "观察池"),
        ("★ M9 Bayonet | Lore (Field-Tested)", "M9 刺刀 | 传说", "久经沙场", "knife", "观察池"),
        ("★ Bayonet | Marble Fade (Factory New)", "刺刀 | 大理石渐变", "崭新出厂", "knife", "观察池"),
        ("★ Talon Knife | Doppler (Factory New)", "锯齿爪刀 | 多普勒", "崭新出厂", "knife", "观察池"),
        ("★ Skeleton Knife | Fade (Factory New)", "骷髅匕首 | 渐变之色", "崭新出厂", "knife", "观察池"),
        ("★ Stiletto Knife | Doppler (Factory New)", "短剑 | 多普勒", "崭新出厂", "knife", "观察池"),
        ("★ Nomad Knife | Fade (Factory New)", "流浪者匕首 | 渐变之色", "崭新出厂", "knife", "观察池"),
        ("Kilowatt Case", "千瓦武器箱", "", "case", "观察池"),
        ("Recoil Case", "反冲武器箱", "", "case", "观察池"),
        ("Dreams & Nightmares Case", "梦魇武器箱", "", "case", "观察池"),
        ("Operation Broken Fang Case", "狂牙大行动武器箱", "", "case", "观察池"),
        ("Operation Riptide Case", "激流大行动武器箱", "", "case", "观察池"),
        ("Clutch Case", "命悬一线武器箱", "", "case", "观察池"),
        ("Prisma 2 Case", "棱彩 2 号武器箱", "", "case", "观察池"),
        ("Danger Zone Case", "头号特训武器箱", "", "case", "观察池"),
        ("Spectrum 2 Case", "光谱 2 号武器箱", "", "case", "观察池"),
        ("Glove Case", "手套武器箱", "", "case", "观察池"),
        ("Sticker | FaZe Clan | Paris 2023", "FaZe | Paris 2023 贴纸", "", "sticker", "观察池"),
        ("Sticker | Vitality | Paris 2023", "Vitality | Paris 2023 贴纸", "", "sticker", "观察池"),
        ("Sticker | Cloud9 | Antwerp 2022", "Cloud9 | Antwerp 2022 贴纸", "", "sticker", "观察池"),
        ("Sticker | FURIA | Antwerp 2022", "FURIA | Antwerp 2022 贴纸", "", "sticker", "观察池"),
        ("Sticker | Team Liquid | Antwerp 2022", "Liquid | Antwerp 2022 贴纸", "", "sticker", "观察池"),
        ("Sticker | Natus Vincere | Stockholm 2021", "NAVI | Stockholm 2021 贴纸", "", "sticker", "观察池"),
        ("Sticker | G2 Esports | Stockholm 2021", "G2 | Stockholm 2021 贴纸", "", "sticker", "观察池"),
        ("Sticker | FaZe Clan | Stockholm 2021", "FaZe | Stockholm 2021 贴纸", "", "sticker", "观察池"),
        ("Stockholm 2021 Legends Sticker Capsule", "Stockholm 2021 传奇贴纸胶囊", "", "capsule", "观察池"),
        ("Antwerp 2022 Legends Sticker Capsule", "Antwerp 2022 传奇贴纸胶囊", "", "capsule", "观察池"),
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
