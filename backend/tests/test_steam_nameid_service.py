import pytest

from app.services.steam_nameid_service import SteamNameIdService


def test_parse_steam_nameid_from_market_page():
    html = "Market_LoadOrderSpread( 176096536 );"

    assert SteamNameIdService().parse(html) == "176096536"


def test_parse_steam_nameid_raises_when_missing():
    with pytest.raises(ValueError):
        SteamNameIdService().parse("<html></html>")
