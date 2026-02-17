"""Tests for livef1.adapters."""
import pytest
from unittest.mock import patch, MagicMock
import livef1.adapters.functions as adapter_functions
from livef1.adapters.livetimingf1_adapter import LivetimingF1adapters, livetimingF1_request, livetimingF1_getdata
from livef1.adapters.other import get_table_from_wikipedia, parse_schedule_from_f1com
from livef1.utils.exceptions import livef1Exception


def test_download_data_requires_season():
    with pytest.raises(livef1Exception, match="season_identifier"):
        adapter_functions.download_data()


def test_download_data_season_only():
    with patch("livef1.adapters.functions.livetimingF1_request") as mock_req:
        mock_req.return_value = {"Meetings": []}
        result = adapter_functions.download_data(season_identifier=2024)
    assert result == {"Meetings": []}
    mock_req.assert_called_once()


def test_download_data_with_location():
    with patch("livef1.adapters.functions.livetimingF1_request") as mock_req:
        mock_req.return_value = {
            "Meetings": [{"Location": "Sakhir", "Sessions": []}],
        }
        result = adapter_functions.download_data(season_identifier=2024, location_identifier="Sakhir")
    assert result["Location"] == "Sakhir"


def test_download_data_location_not_found():
    with patch("livef1.adapters.functions.livetimingF1_request") as mock_req:
        mock_req.return_value = {"Meetings": [{"Location": "Monaco"}]}
        with pytest.raises(livef1Exception, match="not found"):
            adapter_functions.download_data(season_identifier=2024, location_identifier="Sakhir")


def test_livetiming_adapter_get():
    with patch("livef1.adapters.livetimingf1_adapter.requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.content = b'{"Feeds": {}}'
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp
        adapter = LivetimingF1adapters()
        result = adapter.get("2024/Index.json")
    assert "Feeds" in result or "{}" in result


def test_livetimingF1_request():
    with patch("livef1.adapters.livetimingf1_adapter.LivetimingF1adapters") as mock_cls:
        mock_instance = MagicMock()
        mock_instance.get.return_value = '{"Feeds": {"SessionInfo": {}}}'
        mock_cls.return_value = mock_instance
        result = livetimingF1_request("https://example.com/Index.json")
    assert "Feeds" in result


def test_livetimingF1_getdata_stream():
    with patch("livef1.adapters.livetimingf1_adapter.LivetimingF1adapters") as mock_cls:
        mock_instance = MagicMock()
        mock_instance.get.return_value = "000000000001{\"k\":1}\r\n000000000002{\"k\":2}\r\n"
        mock_cls.return_value = mock_instance
        result = livetimingF1_getdata("https://example.com/Stream.jsonStream", stream=True)
    assert isinstance(result, list)
    assert len(result) >= 1
    assert result[0][0] == "000000000001"


def test_get_table_from_wikipedia():
    with patch("livef1.adapters.other.requests.get") as mock_get:
        mock_get.return_value.content = b"<html><table class='wikitable'><caption>Test</caption><tr><th>A</th></tr><tr><td>1</td></tr></table></html>"
        with patch("livef1.adapters.other._parse_tables_from_wikipedia") as mock_parse:
            import pandas as pd
            mock_parse.return_value = {"Test": pd.DataFrame({"A": [1]})}
            result = get_table_from_wikipedia("https://en.wikipedia.org/wiki/Test", "Test")
    assert result is not None
    assert "A" in result.columns


def test_parse_schedule_from_f1com_mocked():
    with patch("livef1.adapters.other.requests.get") as mock_get:
        mock_get.return_value.content = b"<html><body><a class='group' href='/race/1'><span class='typography-module_body-xs-semibold__Fyfwn'>Bahrain</span><span class='CountryFlag-module_flag__Y-X37'><title>Flag of Bahrain</title></span></a></body></html>"
        with patch("livef1.adapters.other.BeautifulSoup") as mock_bs:
            mock_soup = MagicMock()
            mock_soup.find_all.return_value = []
            mock_bs.return_value = mock_soup
            result = parse_schedule_from_f1com(2024)
    import pandas as pd
    assert isinstance(result, pd.DataFrame)
    assert "Meeting Shortname" in result.columns or len(result) == 0
