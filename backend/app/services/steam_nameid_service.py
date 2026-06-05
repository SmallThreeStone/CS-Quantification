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
