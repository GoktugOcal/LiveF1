"""Tests for livef1.models.session.Session."""
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from livef1.models.session import Session
from livef1.data_processing.data_models import BronzeTable
from livef1.data_processing.lakes import DataLake


def test_session_constructor_minimal():
    with patch("livef1.models.session.helper.build_session_endpoint", return_value="https://example.com/session"):
        session = Session(
            key=9465,
            name="Race",
            path="2024/2024-03-02_Bahrain/2024-03-02_Race",
        )
    assert session.key == 9465
    assert session.name == "Race"
    assert hasattr(session, "data_lake")
    assert hasattr(session, "full_path")
    assert session.laps is None
    assert session.carTelemetry is None


def test_session_check_data_name():
    with patch("livef1.models.session.helper.build_session_endpoint", return_value="https://example.com/session"):
        session = Session(key=9465, name="Race", path="x")
    session.topic_names_info = {
        "TimingData": {"key": "Timing_Data"},
        "CarData.z": {"key": "Car_Data"},
    }
    assert session.check_data_name("TimingData") == "TimingData"
    assert session.check_data_name("timing_data") == "TimingData"
    assert session.check_data_name("CarData.z") == "CarData.z"


def test_session_get_laps_none():
    with patch("livef1.models.session.helper.build_session_endpoint", return_value="https://example.com/session"):
        session = Session(key=9465, name="Race", path="x")
    session.laps = None
    assert session.get_laps() is None


def test_session_get_laps_returns_laps():
    with patch("livef1.models.session.helper.build_session_endpoint", return_value="https://example.com/session"):
        session = Session(key=9465, name="Race", path="x")
    session.laps = pd.DataFrame({"LapNo": [1], "DriverNo": [1]})
    result = session.get_laps()
    assert result is not None
    assert len(result) == 1


def test_session_get_car_telemetry_none():
    with patch("livef1.models.session.helper.build_session_endpoint", return_value="https://example.com/session"):
        session = Session(key=9465, name="Race", path="x")
    session.carTelemetry = None
    assert session.get_car_telemetry() is None


def test_session_get_car_telemetry_returns_df():
    with patch("livef1.models.session.helper.build_session_endpoint", return_value="https://example.com/session"):
        session = Session(key=9465, name="Race", path="x")
    session.carTelemetry = pd.DataFrame({"DriverNo": [1], "Speed": [200]})
    result = session.get_car_telemetry()
    assert result is not None
    assert len(result) == 1


def test_session_get_data_from_cache():
    with patch("livef1.models.session.helper.build_session_endpoint", return_value="https://example.com/session"):
        session = Session(key=9465, name="Race", path="x")
    session.topic_names_info = {"TimingData": {"key": "Timing_Data", "default_is_stream": True}}
    session.data_lake.metadata = {"TimingData": {"table_type": "bronze", "generated": False}}
    bt = BronzeTable("TimingData", data={}, parsed_data=[{"SessionKey": 9465}], data_lake=session.data_lake)
    session.data_lake.put("bronze", "TimingData", bt)
    session.data_lake.metadata["TimingData"] = {"table_type": "bronze", "generated": False}
    result = session.get_data("TimingData", force=False)
    assert result is not None
    assert hasattr(result, "columns") or hasattr(result, "index")


def test_session_create_silver_table_decorator():
    with patch("livef1.models.session.helper.build_session_endpoint", return_value="https://example.com/session"):
        session = Session(key=9465, name="Race", path="x")
    session.topic_names_info = {"TimingData": {"key": "Timing_Data"}}
    session.data_lake.metadata["TimingData"] = {"table_type": "bronze", "generated": False}
    bt = BronzeTable("TimingData", data={}, parsed_data=[{"SessionKey": 9465}], data_lake=session.data_lake)
    session.data_lake.put("bronze", "TimingData", bt)

    @session.create_silver_table(table_name="CustomLaps", source_tables=["TimingData"], include_session=True)
    def custom_laps(_session, TimingData):
        return TimingData.head(1)

    assert "CustomLaps" in session.data_lake.metadata
    assert session.data_lake.get("silver", "CustomLaps") is not None
