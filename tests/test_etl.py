"""Tests for livef1.data_processing.etl."""
import pytest
from unittest.mock import MagicMock
from livef1.data_processing.etl import livef1SessionETL, function_map
from livef1.utils.exceptions import MissingFunctionError, ETLError


def test_etl_init(mock_session):
    etl = livef1SessionETL(mock_session)
    assert etl.session is mock_session
    assert etl.function_map is function_map


def test_function_map_has_expected_keys():
    assert "SessionInfo" in function_map
    assert "TimingData" in function_map
    assert "DriverList" in function_map
    assert "RaceControlMessages" in function_map
    assert "CarData.z" in function_map


def test_unified_parse_known_title(mock_session):
    etl = livef1SessionETL(mock_session)
    data = [("0", {"Status": "Started"})]
    records = list(etl.unified_parse("SessionStatus", data))
    assert len(records) == 1
    assert records[0]["SessionKey"] == mock_session.key
    assert records[0]["status"] == "Started"


def test_unified_parse_unknown_title_raises(mock_session):
    etl = livef1SessionETL(mock_session)
    with pytest.raises(MissingFunctionError, match="No parser"):
        list(etl.unified_parse("UnknownTopic", []))


def test_unified_parse_none_parser_raises(mock_session):
    etl = livef1SessionETL(mock_session)
    with pytest.raises(ETLError, match="Parser of ArchiveStatus failed"):
        list(etl.unified_parse("ArchiveStatus", []))


def test_clean_data():
    etl = livef1SessionETL(MagicMock())
    data = [{"a": 1}, {"a": 2}]
    result = etl.clean_data(data)
    assert result == data


def test_aggregate_data():
    etl = livef1SessionETL(MagicMock())
    data = [{"a": 1}, {"a": 2}]
    result = etl.aggregate_data(data)
    assert result == data
