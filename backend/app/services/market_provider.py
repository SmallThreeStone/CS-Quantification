import random
from dataclasses import dataclass
from datetime import datetime

import httpx

from app.config import settings


@dataclass
class Quote:
    market_hash_name: str
    lowest_price: float
    sell_count: int
    highest_buy_price: float
    buy_count: int
    volume_24h: int
    avg_price_24h: float
    captured_at: datetime
    raw_payload: dict


class MockMarketProvider:
    def __init__(self) -> None:
        self.base = {
            "★ Specialist Gloves | Emerald Web (Field-Tested)": {
                "lowest_price": 6880.0,
                "sell_count": 42,
                "highest_buy_price": 6420.0,
                "buy_count": 18,
                "volume_24h": 7,
                "avg_price_24h": 6750.0,
            },
            "★ Sport Gloves | Vice (Field-Tested)": {
                "lowest_price": 8120.0,
                "sell_count": 31,
                "highest_buy_price": 7790.0,
                "buy_count": 15,
                "volume_24h": 5,
                "avg_price_24h": 8055.0,
            },
        }

    def fetch_quote(self, market_hash_name: str) -> Quote:
        seed = sum(ord(char) for char in market_hash_name) + datetime.utcnow().minute
        random.seed(seed)
        item = self.base.get(market_hash_name, next(iter(self.base.values())))
        sell_shift = random.randint(-12, 18)
        buy_shift = random.randint(-7, 10)
        price_shift = random.uniform(-0.025, 0.025)
        lowest_price = round(item["lowest_price"] * (1 + price_shift), 2)
        highest_buy_price = round(item["highest_buy_price"] * (1 + price_shift * 0.7), 2)
        return Quote(
            market_hash_name=market_hash_name,
            lowest_price=lowest_price,
            sell_count=max(1, item["sell_count"] + sell_shift),
            highest_buy_price=highest_buy_price,
            buy_count=max(1, item["buy_count"] + buy_shift),
            volume_24h=max(0, item["volume_24h"] + random.randint(-2, 5)),
            avg_price_24h=round((lowest_price + item["avg_price_24h"]) / 2, 2),
            captured_at=datetime.utcnow(),
            raw_payload={"provider": "mock"},
        )


class SteamMarketProvider:
    def __init__(self) -> None:
        self.fallback = MockMarketProvider()

    def fetch_quote(self, market_hash_name: str) -> Quote:
        response = httpx.get(
            "https://steamcommunity.com/market/priceoverview/",
            params={"appid": 730, "currency": 23, "market_hash_name": market_hash_name},
            timeout=8,
        )
        response.raise_for_status()
        payload = response.json()
        if not payload.get("success"):
            return self.fallback.fetch_quote(market_hash_name)
        fallback = self.fallback.fetch_quote(market_hash_name)
        lowest_price = self._money_to_float(payload.get("lowest_price")) or fallback.lowest_price
        volume_text = str(payload.get("volume") or "").replace(",", "")
        volume_24h = int(volume_text) if volume_text.isdigit() else fallback.volume_24h
        return Quote(
            market_hash_name=market_hash_name,
            lowest_price=lowest_price,
            sell_count=fallback.sell_count,
            highest_buy_price=fallback.highest_buy_price,
            buy_count=fallback.buy_count,
            volume_24h=volume_24h,
            avg_price_24h=self._money_to_float(payload.get("median_price")) or fallback.avg_price_24h,
            captured_at=datetime.utcnow(),
            raw_payload={"provider": "steam_priceoverview", "payload": payload},
        )

    def _money_to_float(self, value: str | None) -> float | None:
        if not value:
            return None
        normalized = (
            value.replace("¥", "")
            .replace("￥", "")
            .replace("RMB", "")
            .replace(",", "")
            .strip()
        )
        try:
            return round(float(normalized), 2)
        except ValueError:
            return None


def get_market_provider() -> MockMarketProvider | SteamMarketProvider:
    if settings.market_provider.lower() == "steam":
        return SteamMarketProvider()
    return MockMarketProvider()
