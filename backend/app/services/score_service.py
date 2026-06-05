from app.models import Alert, MarketSnapshot


def status_from_alert(alert: Alert | None) -> str:
    if alert is None:
        return "横盘观察"
    return alert.direction


def score_from_snapshot(snapshot: MarketSnapshot | None, alert: Alert | None) -> tuple[int, int]:
    if snapshot is None:
        return 50, 50
    liquidity = min(30, snapshot.volume_24h * 3)
    spread = snapshot.lowest_price - snapshot.highest_buy_price
    spread_penalty = 15 if spread / max(snapshot.lowest_price, 1) > 0.08 else 0
    buy_score = 45 + liquidity - spread_penalty
    sell_score = 45 + liquidity // 2
    if alert and alert.direction == "偏买入机会":
        buy_score += 18
    if alert and alert.direction == "偏卖压风险":
        sell_score += 18
        buy_score -= 12
    if alert and alert.direction == "偏扫货拉升":
        buy_score += 10
        sell_score += 8
    return max(0, min(100, buy_score)), max(0, min(100, sell_score))
