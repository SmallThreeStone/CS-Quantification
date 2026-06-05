import re
from urllib.parse import quote

import httpx


class SteamNameIdService:
    def discover(self, market_hash_name: str) -> str:
        response = httpx.get(
            f"https://steamcommunity.com/market/listings/730/{quote(market_hash_name)}",
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10,
        )
        response.raise_for_status()
        return self.parse(response.text)

    def parse(self, html: str) -> str:
        match = re.search(r"Market_LoadOrderSpread\(\s*(\d+)\s*\)", html)
        if match is None:
            raise ValueError("steam item_nameid not found")
        return match.group(1)

    def validate_orderbook(self, steam_item_nameid: str) -> dict:
        if not steam_item_nameid:
            raise ValueError("missing steam item_nameid")
        payload = self.fetch_orderbook(steam_item_nameid)
        orderbook = self.parse_orderbook(payload)
        if orderbook is None:
            raise ValueError("steam orderbook is empty")
        return orderbook

    def fetch_orderbook(self, steam_item_nameid: str) -> dict:
        response = httpx.get(
            "https://steamcommunity.com/market/itemordershistogram",
            params={
                "country": "CN",
                "language": "schinese",
                "currency": 23,
                "item_nameid": steam_item_nameid,
            },
            timeout=8,
        )
        response.raise_for_status()
        return response.json()

    def parse_orderbook(self, payload: dict) -> dict | None:
        sell_orders = payload.get("sell_order_graph") or []
        buy_orders = payload.get("buy_order_graph") or []
        if not sell_orders and not buy_orders:
            return None
        sell_count = self.total_order_count(sell_orders)
        buy_count = self.total_order_count(buy_orders)
        highest_buy_price = float(buy_orders[0][0]) if buy_orders else 0
        return {"sell_count": sell_count, "buy_count": buy_count, "highest_buy_price": round(highest_buy_price, 2)}

    def total_order_count(self, rows: list[list]) -> int:
        counts = []
        for row in rows:
            if len(row) >= 2:
                try:
                    counts.append(int(float(row[1])))
                except (TypeError, ValueError):
                    pass
        return max(counts, default=0)
