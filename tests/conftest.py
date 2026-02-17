"""Shared pytest fixtures for LiveF1 tests."""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import MagicMock


@pytest.fixture
def session_path():
    """Minimal session path dict as returned by API."""
    return "2024/2024-03-02_Bahrain_Grand_Prix/2024-03-02_Race"


@pytest.fixture
def season_data():
    """Minimal season index response (Meetings list)."""
    return {
        "Year": 2024,
        "Meetings": [
            {
                "Key": 1212,
                "Code": "BAH",
                "Number": 1,
                "Location": "Sakhir",
                "OfficialName": "Bahrain Grand Prix",
                "Name": "Bahrain",
                "Country": {"Key": 1, "Code": "BHR", "Name": "Bahrain"},
                "Circuit": {"Key": 3, "ShortName": "Sakhir"},
                "Sessions": [
                    {
                        "Key": 9465,
                        "Type": "Race",
                        "Number": 5,
                        "Name": "Race",
                        "StartDate": "2024-03-02T15:00:00Z",
                        "EndDate": "2024-03-02T17:00:00Z",
                        "GmtOffset": "+03:00",
                        "Path": "2024-03-02_Race",
                    }
                ],
            }
        ]
    }


@pytest.fixture
def meeting_data(season_data):
    """Single meeting from season data."""
    return season_data["Meetings"][0]


@pytest.fixture
def session_data(meeting_data):
    """Single session from meeting data."""
    return meeting_data["Sessions"][0]


@pytest.fixture
def sample_laps_df():
    """Minimal laps DataFrame for silver_functions."""
    return pd.DataFrame({
        "SessionKey": [9465] * 4,
        "DriverNo": [1, 1, 44, 44],
        "LapNo": [1, 2, 1, 2],
        "timestamp": pd.to_timedelta(["0 days 01:30:00", "0 days 01:31:00", "0 days 01:30:05", "0 days 01:31:05"]),
        "Speed": [280.0, 285.0, 275.0, 282.0],
        "X": [100.0, 200.0, 105.0, 205.0],
        "Y": [50.0, 60.0, 52.0, 62.0],
        "LapStartTime": pd.to_timedelta(["0 days 01:29:00", "0 days 01:30:00", "0 days 01:29:05", "0 days 01:30:05"]),
    })


@pytest.fixture
def sample_track_status_df():
    """Minimal track status DataFrame."""
    return pd.DataFrame({
        "timestamp": pd.to_timedelta(["0 days 01:29:00", "0 days 01:30:30"]),
        "Status": ["1", "2"],
        "Message": ["Green", "Yellow"],
    })


@pytest.fixture
def sample_telemetry_df():
    """Minimal telemetry DataFrame with timestamp and SessionKey."""
    return pd.DataFrame({
        "SessionKey": [9465] * 3,
        "timestamp": pd.to_timedelta(["0 days 01:30:00", "0 days 01:30:01", "0 days 01:30:02"]),
        "Speed": [100, 150, 200],
        "DriverNo": [1, 1, 1],
    })


@pytest.fixture
def sample_tmg_df():
    """Minimal timing/line position DataFrame."""
    return pd.DataFrame({
        "timestamp": pd.to_timedelta(["0 days 01:30:00", "0 days 01:30:01"]),
        "Position": [1, 1],
    })


@pytest.fixture
def mock_session():
    """Mock Session with minimal attributes for unit tests."""
    session = MagicMock()
    session.key = 9465
    session.path = "2024/2024-03-02_Bahrain_Grand_Prix/2024-03-02_Race"
    session.full_path = "https://livetiming.formula1.com/static/2024/2024-03-02_Bahrain_Grand_Prix/2024-03-02_Race"
    session.topic_names_info = {
        "TimingData": {"key": "Timing_Data", "KeyFramePath": "TimingData.json", "StreamPath": "TimingData.jsonStream", "default_is_stream": True},
        "CarData.z": {"key": "Car_Data", "KeyFramePath": "CarData.z.json", "StreamPath": "CarData.z.jsonStream", "default_is_stream": True},
        "DriverList": {"key": "Driver_List", "KeyFramePath": "DriverList.json", "StreamPath": "DriverList.jsonStream", "default_is_stream": False},
    }
    session.drivers = {}
    session.meeting = MagicMock()
    session.meeting.name = "Bahrain"
    session.meeting.circuit = MagicMock()
    return session


@pytest.fixture
def sample_parse_stream_data():
    """Stream format: list of (key, value) pairs."""
    return [
        ("000000000001", '{"SessionKey": 9465}'),
        ("000000000002", '{"DriverNo": "1", "Tla": "VER"}'),
    ]


@pytest.fixture
def sample_rcm_df():
    """Minimal race control messages DataFrame for generate_race_control_messages_table."""
    return pd.DataFrame({
        "SessionKey": [9465],
        "timestamp": [pd.Timedelta("1h30m")],
        "Utc": ["2024-03-02T15:30:00Z"],
        "Category": ["Other"],
        "Scope": ["All"],
        "Status": ["1"],
        "Flag": [None],
        "Message": ["RACE CONTROL MESSAGE"],
        "Lap": [1],
        "RacingNumber": ["1"],
    })
