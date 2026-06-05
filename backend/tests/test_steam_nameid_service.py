import pytest

from app.services.steam_nameid_service import SteamNameIdService


def test_parse_steam_nameid_from_market_page():
    html = "Market_LoadOrderSpread( 176096536 );"

    assert SteamNameIdService().parse(html) == "176096536"


def test_parse_steam_nameid_raises_when_missing():
    with pytest.raises(ValueError):
        SteamNameIdService().parse("<html></html>")


def test_parse_orderbook_returns_depth_metrics():
    payload = {
        "sell_order_graph": [[101.0, 3, "3"], [102.0, 8, "8"]],
        "buy_order_graph": [[99.0, 4, "4"], [98.0, 9, "9"]],
    }

    orderbook = SteamNameIdService().parse_orderbook(payload)

    assert orderbook == {"sell_count": 8, "buy_count": 9, "highest_buy_price": 99.0}


def test_validate_orderbook_raises_when_nameid_missing():
    with pytest.raises(ValueError):
        SteamNameIdService().validate_orderbook("")
