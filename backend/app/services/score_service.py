from app.models import Alert, MarketSnapshot


def decision_from_scores(
    snapshot: MarketSnapshot | None,
    status: str,
    adjusted_buy_score: int,
    adjusted_sell_score: int,
    quality_ratio: float | None,
) -> dict[str, int | str]:
    if snapshot is None:
        return {"action": "观望", "confidence": 20, "reason": "暂无行情快照"}
    if quality_ratio is not None and quality_ratio < 0.3:
        return {"action": "观望", "confidence": 35, "reason": "数据可信度偏低"}
    if adjusted_sell_score >= 72 and adjusted_sell_score - adjusted_buy_score >= 8:
        return {"action": "卖出", "confidence": adjusted_sell_score, "reason": "卖出分明显高于买入分"}
    if adjusted_buy_score >= 72 and adjusted_buy_score - adjusted_sell_score >= 8:
        return {"action": "买入", "confidence": adjusted_buy_score, "reason": "买入分明显高于卖出分"}
    if status in {"偏卖压风险", "偏流动性异常"} and adjusted_sell_score >= 68:
        return {"action": "卖出", "confidence": adjusted_sell_score, "reason": status}
    if status in {"偏买入机会", "偏扫货拉升"} and adjusted_buy_score >= 68:
        return {"action": "买入", "confidence": adjusted_buy_score, "reason": status}
    if max(adjusted_buy_score, adjusted_sell_score) < 55:
        return {"action": "观望", "confidence": max(adjusted_buy_score, adjusted_sell_score), "reason": "参考分不足"}
    return {"action": "持有", "confidence": max(adjusted_buy_score, adjusted_sell_score), "reason": "买卖分接近，等待更明确异动"}


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
    if alert and alert.direction == "偏流动性异常":
        buy_score -= 8
        sell_score += 6
    return max(0, min(100, buy_score)), max(0, min(100, sell_score))
