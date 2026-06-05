import json
import random
import re
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
            raw_payload={
                "provider": "mock",
                "source_quality": {
                    "real_fields": [],
                    "fallback_fields": [
                        "lowest_price",
                        "sell_count",
                        "highest_buy_price",
                        "buy_count",
                        "volume_24h",
                        "avg_price_24h",
                    ],
                    "is_fallback": True,
                },
            },
        )


class SteamMarketProvider:
    def __init__(self) -> None:
        self.fallback = MockMarketProvider()
        self.item_nameids = self._load_item_nameids()

    def fetch_quote(self, market_hash_name: str) -> Quote:
        payload = self._priceoverview(market_hash_name)
        if not payload.get("success"):
            quote = self.fallback.fetch_quote(market_hash_name)
            quote.raw_payload["provider"] = "steam_priceoverview"
            quote.raw_payload["source_quality"]["is_fallback"] = True
            quote.raw_payload["fallback_reason"] = "steam response success=false"
            quote.raw_payload["payload"] = payload
            return quote
        fallback = self.fallback.fetch_quote(market_hash_name)
        lowest_price = self._money_to_float(payload.get("lowest_price")) or fallback.lowest_price
        volume_text = str(payload.get("volume") or "").replace(",", "")
        volume_24h = int(volume_text) if volume_text.isdigit() else fallback.volume_24h
        real_fields = []
        fallback_fields = ["sell_count", "highest_buy_price", "buy_count"]
        orderbook_payload = None
        orderbook = None
        orderbook_error = ""
        if settings.steam_orderbook_enabled:
            try:
                orderbook_payload = self._orderbook(market_hash_name)
                orderbook = self._parse_orderbook(orderbook_payload)
            except Exception as exc:
                orderbook_error = str(exc)
        if payload.get("lowest_price"):
            real_fields.append("lowest_price")
        else:
            fallback_fields.append("lowest_price")
        if payload.get("volume"):
            real_fields.append("volume_24h")
        else:
            fallback_fields.append("volume_24h")
        if payload.get("median_price"):
            real_fields.append("avg_price_24h")
        else:
            fallback_fields.append("avg_price_24h")
        if orderbook is not None:
            for field in ["sell_count", "highest_buy_price", "buy_count"]:
                if field in fallback_fields:
                    fallback_fields.remove(field)
                real_fields.append(field)
        return Quote(
            market_hash_name=market_hash_name,
            lowest_price=lowest_price,
            sell_count=orderbook["sell_count"] if orderbook else fallback.sell_count,
            highest_buy_price=orderbook["highest_buy_price"] if orderbook else fallback.highest_buy_price,
            buy_count=orderbook["buy_count"] if orderbook else fallback.buy_count,
            volume_24h=volume_24h,
            avg_price_24h=self._money_to_float(payload.get("median_price")) or fallback.avg_price_24h,
            captured_at=datetime.utcnow(),
            raw_payload={
                "provider": "steam_priceoverview",
                "payload": payload,
                "orderbook_payload": orderbook_payload,
                "orderbook_error": orderbook_error,
                "source_quality": {
                    "real_fields": real_fields,
                    "fallback_fields": fallback_fields,
                    "is_fallback": False,
                },
            },
        )

    def _priceoverview(self, market_hash_name: str) -> dict:
        response = httpx.get(
            "https://steamcommunity.com/market/priceoverview/",
            params={"appid": 730, "currency": 23, "market_hash_name": market_hash_name},
            timeout=8,
        )
        response.raise_for_status()
        return response.json()

    def _orderbook(self, market_hash_name: str) -> dict:
        item_nameid = self.item_nameids.get(market_hash_name)
        if not item_nameid:
            raise ValueError("missing steam item_nameid mapping")
        response = httpx.get(
            "https://steamcommunity.com/market/itemordershistogram",
            params={
                "country": "CN",
                "language": "schinese",
                "currency": 23,
                "item_nameid": item_nameid,
            },
            timeout=8,
        )
        response.raise_for_status()
        return response.json()

    def _parse_orderbook(self, payload: dict) -> dict | None:
        sell_orders = payload.get("sell_order_graph") or []
        buy_orders = payload.get("buy_order_graph") or []
        if not sell_orders and not buy_orders:
            return None
        sell_count = self._total_order_count(sell_orders)
        buy_count = self._total_order_count(buy_orders)
        highest_buy_price = float(buy_orders[0][0]) if buy_orders else 0
        return {"sell_count": sell_count, "buy_count": buy_count, "highest_buy_price": round(highest_buy_price, 2)}

    def _total_order_count(self, rows: list[list]) -> int:
        counts = []
        for row in rows:
            if len(row) >= 2:
                try:
                    counts.append(int(float(row[1])))
                except (TypeError, ValueError):
                    pass
        return max(counts, default=0)

    def _load_item_nameids(self) -> dict[str, str]:
        try:
            payload = json.loads(settings.steam_orderbook_item_nameids)
        except json.JSONDecodeError:
            return {}
        return {str(key): str(value) for key, value in payload.items()}

    def _money_to_float(self, value: str | None) -> float | None:
        if not value:
            return None
        match = re.search(r"\d+(?:,\d{3})*(?:\.\d+)?", value)
        if match is None:
            return None
        normalized = match.group(0).replace(",", "")
        try:
            return round(float(normalized), 2)
        except ValueError:
            return None


def get_market_provider() -> MockMarketProvider | SteamMarketProvider:
    if settings.market_provider.lower() == "steam":
        return SteamMarketProvider()
    return MockMarketProvider()
