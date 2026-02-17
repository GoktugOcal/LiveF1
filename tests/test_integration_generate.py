"""
Integration-style test: get_season -> get_meeting -> get_session with dummy data, then run generate().
All I/O is mocked so no network calls are made.
"""
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
import livef1
from livef1.api import get_season, get_meeting, get_session


def _minimal_position_z_records():
    return [
        {"SessionKey": 9465, "timestamp": "0", "Utc": "2024-03-02T15:00:00Z", "DriverNo": "1", "X": 0, "Y": 0, "Z": 0},
        {"SessionKey": 9465, "timestamp": "1", "Utc": "2024-03-02T15:00:01Z", "DriverNo": "1", "X": 10, "Y": 10, "Z": 0},
    ]


def _minimal_car_data_z_records():
    return [
        {"SessionKey": 9465, "timestamp": "0", "Utc": "2024-03-02T15:00:00Z", "DriverNo": "1", "Speed": 100},
        {"SessionKey": 9465, "timestamp": "1", "Utc": "2024-03-02T15:00:01Z", "DriverNo": "1", "Speed": 150},
    ]


def _minimal_session_data_records():
    return [
        {"SessionKey": 9465, "SessionStatus": "Started", "Utc": "2024-03-02T15:00:00Z"},
    ]


def _minimal_timing_data_records():
    return [
        {"SessionKey": 9465, "timestamp": "0", "DriverNo": "1", "NumberOfLaps": 1, "LastLapTime_Value": None},
    ]


def _minimal_rcm_records():
    return [
        {"SessionKey": 9465, "timestamp": "0", "Category": "Other", "Message": "Test"},
    ]


def _minimal_tyre_stint_records():
    return [
        {"session_key": 9465, "timestamp": "0", "DriverNo": "1", "Compound": "SOFT", "TotalLaps": 0},
    ]


def _minimal_track_status_records():
    return [
        {"timestamp": "0", "Status": "1", "Message": "Green"},
    ]


def _dummy_load_single_data(dataName, session, stream):
    """Return minimal (name, raw, parsed) so bronze tables can be created."""
    raw = {}
    if dataName == "Position.z":
        parsed = _minimal_position_z_records()
    elif dataName == "CarData.z":
        parsed = _minimal_car_data_z_records()
    elif dataName in ("Session_Data", "SessionData"):
        parsed = _minimal_session_data_records()
    elif dataName == "SessionStatus":
        parsed = [{"SessionKey": 9465, "timestamp": "0", "status": "Started", "Utc": "2024-03-02T15:00:00Z"}]
    elif dataName == "TimingData":
        parsed = _minimal_timing_data_records()
    elif dataName == "RaceControlMessages":
        parsed = _minimal_rcm_records()
    elif dataName == "TyreStintSeries":
        parsed = _minimal_tyre_stint_records()
    elif dataName == "TrackStatus":
        parsed = _minimal_track_status_records()
    else:
        parsed = [{"SessionKey": 9465}]
    return dataName, raw, parsed


@pytest.fixture
def mock_circuit_requests():
    """Mock circuit start coordinates and circuit data API."""
    start_coords = {"Sakhir": {"start_coordinates": [100.0, 50.0], "start_direction": [1.0, 1.0]}}
    circuits_list = {
        "1": {"name": "Sakhir", "circuitKey": 3, "years": [2024]},
    }
    circuit_corners = {
        "corners": [
            {"number": 1, "length": 100, "x": 0, "y": 0, "trackPosition": {"x": 0, "y": 0}},
            {"number": 2, "length": 200, "x": 10, "y": 10, "trackPosition": {"x": 10, "y": 10}},
        ]
    }

    def fake_get(url, **kwargs):
        resp = MagicMock()
        resp.status_code = 200
        if "starting_coordinates" in url or "START_COORDINATES" in str(url):
            resp.json.return_value = start_coords
        elif "api/v1/circuits" in url and "/circuits/" not in url:
            resp.json.return_value = circuits_list
        elif "api/v1/circuits" in url:
            resp.json.return_value = circuit_corners
        else:
            resp.json.return_value = {}
        return resp

    return fake_get


@pytest.fixture
def index_feeds():
    """Minimal Feeds dict for session Index.json (must include all topics required by generate())."""
    feeds = {
        "SessionInfo": {"KeyFramePath": "SessionInfo.json", "StreamPath": "SessionInfo.jsonStream"},
        "TrackStatus": {"KeyFramePath": "TrackStatus.json", "StreamPath": "TrackStatus.jsonStream"},
        "TimingData": {"KeyFramePath": "TimingData.json", "StreamPath": "TimingData.jsonStream"},
        "RaceControlMessages": {"KeyFramePath": "RCM.json", "StreamPath": "RCM.jsonStream"},
        "TyreStintSeries": {"KeyFramePath": "TyreStint.json", "StreamPath": "TyreStint.jsonStream"},
        "CarData.z": {"KeyFramePath": "CarData.z.json", "StreamPath": "CarData.z.jsonStream"},
        "Position.z": {"KeyFramePath": "Position.z.json", "StreamPath": "Position.z.jsonStream"},
        "SessionData": {"KeyFramePath": "SessionData.json", "StreamPath": "SessionData.jsonStream"},
        "SessionStatus": {"KeyFramePath": "SessionStatus.json", "StreamPath": "SessionStatus.jsonStream"},
        "DriverList": {"KeyFramePath": "DriverList.json", "StreamPath": "DriverList.jsonStream"},
    }
    return {"Feeds": feeds}


def test_get_season_meeting_session_and_generate_with_dummy_data(
    season_data,
    mock_circuit_requests,
    index_feeds,
):
    """Use dummy inputs to get season, meeting, session and run generate(silver=True)."""
    with patch("livef1.api.download_data", return_value=season_data):
        with patch("livef1.models.season.download_data", return_value=season_data):
            with patch("livef1.models.circuit.requests.get", side_effect=mock_circuit_requests):
                with patch("livef1.api.find_most_similar_vectorized", return_value={"row_index": 0}):
                    with patch("livef1.api.print_found_model"):
                        season = get_season(2024)
    assert season is not None
    assert hasattr(season, "meetings")
    assert len(season.meetings) >= 1

    with patch("livef1.api.get_season", return_value=season):
        with patch("livef1.api.find_most_similar_vectorized", return_value={"row_index": 0}):
            with patch("livef1.api.print_found_model"):
                meeting = get_meeting(2024, meeting_identifier="Bahrain")
    assert meeting is not None
    assert hasattr(meeting, "sessions")

    session_key = 9465
    session_obj = None
    for name, s in meeting.sessions.items():
        if s.key == session_key:
            session_obj = s
            break
    if session_obj is None:
        session_obj = list(meeting.sessions.values())[0]

    with patch("livef1.models.session.livetimingF1_request", return_value=index_feeds):
        with patch("livef1.models.session.livetimingF1_getdata") as mock_getdata:
            mock_getdata.return_value = {"1": {"RacingNumber": "1", "Tla": "VER", "FirstName": "Max", "LastName": "Verstappen"}}
            session_obj.load_session_data()

    assert hasattr(session_obj, "topic_names_info")
    assert hasattr(session_obj, "drivers")

    def mock_load_circuit_data():
        if not hasattr(session_obj.meeting.circuit, "track_regions"):
            session_obj.meeting.circuit._raw_circuit_data = {"corners": []}
            session_obj.meeting.circuit.track_regions = pd.DataFrame({
                "name": ["T1"], "corner_start": [0], "corner_end": [100],
            })
        session_obj.data_lake.create_bronze_table(
            table_name="track_regions",
            raw_data=getattr(session_obj.meeting.circuit, "_raw_circuit_data", {}),
            parsed_data=session_obj.meeting.circuit.track_regions,
        )

    with patch.object(session_obj, "_load_circuit_data", side_effect=mock_load_circuit_data):
        with patch("livef1.models.session.load_single_data", side_effect=_dummy_load_single_data):
            session_obj.generate(silver=True, gold=False)

    assert session_obj.first_datetime is not None
    assert session_obj.session_start_datetime is not None
    assert session_obj.data_lake._check_circular_dependencies() is True
    assert "laps" in session_obj.data_lake.metadata or "raceControlMessages" in session_obj.data_lake.metadata
