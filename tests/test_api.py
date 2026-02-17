"""Tests for livef1.api (get_season, get_meeting, get_session)."""
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from livef1.api import get_season, get_meeting, get_session
from livef1.utils.exceptions import ArgumentError, LiveF1Error


@pytest.fixture
def mock_season_data(season_data):
    return season_data


def test_get_season_mocked(mock_season_data):
    with patch("livef1.api.download_data", return_value=mock_season_data) as mock_dl:
        with patch("livef1.api.Season") as mock_season_class:
            mock_season_instance = MagicMock()
            mock_season_class.return_value = mock_season_instance
            season = get_season(2024)
            mock_dl.assert_called()
            mock_season_class.assert_called_once()
    assert season is mock_season_instance


def test_get_meeting_requires_args():
    with patch("livef1.api.get_season") as mock_get_season:
        mock_season = MagicMock()
        mock_season.meetings = []
        mock_get_season.return_value = mock_season
        with pytest.raises((ArgumentError, IndexError)):
            get_meeting(2024)


def test_get_meeting_by_offname(mock_season_data):
    with patch("livef1.api.get_season") as mock_get_season:
        mock_season = MagicMock()
        mock_meeting = MagicMock()
        mock_meeting.officialname = "Bahrain Grand Prix"
        mock_season.meetings = [mock_meeting]
        mock_season.meetings_table = MagicMock()
        mock_get_season.return_value = mock_season
        meeting = get_meeting(2024, meeting_offname="Bahrain Grand Prix")
        assert meeting is mock_meeting


def test_get_meeting_by_identifier_mocked(mock_season_data):
    mock_meeting = MagicMock()
    mock_meeting.key = 1212
    with patch("livef1.api.get_season") as mock_get_season:
        df = pd.DataFrame({
            "Meeting Key": [1212],
            "Meeting Offname": ["Bahrain"],
            "Meeting Name": ["Bahrain"],
            "Meeting Circuit Shortname": ["Sakhir"],
        })
        mock_season = MagicMock()
        mock_season.meetings_table = df
        mock_season.season_table = df
        mock_season.meetings = [mock_meeting]
        mock_get_season.return_value = mock_season
        with patch("livef1.api.find_most_similar_vectorized", return_value={"row_index": 0}):
            with patch("livef1.api.print_found_model"):
                meeting = get_meeting(2024, meeting_identifier="Bahrain")
        assert meeting is mock_meeting


def test_get_session_requires_args():
    with pytest.raises(ArgumentError, match="session_identifier|session_key"):
        get_session(2024, meeting_identifier="Bahrain")


def test_get_session_mocked():
    import livef1.api as api_mod
    mock_meeting = MagicMock()
    mock_session = MagicMock()
    mock_session.key = 9465
    mock_meeting.sessions = {"Race": mock_session}
    mock_meeting.sessions_table = pd.DataFrame({"session_name": ["Race"]}, index=pd.Index([9465], name="session_key"))
    with patch.object(api_mod, "get_meeting", return_value=mock_meeting):
        with patch.object(api_mod, "find_most_similar_vectorized", return_value={"row_index": 0}):
            with patch.object(api_mod, "print_found_model"):
                with patch.object(mock_session, "load_session_data"):
                    session = get_session(2024, meeting_identifier="Bahrain", session_identifier="Race")
    assert session is mock_session


# ---------- Explicit get_meeting tests ----------


def test_get_meeting_by_meeting_key_explicit():
    """get_meeting(season, meeting_key=N) returns the meeting with that key."""
    required_cols = ["Meeting Offname", "Meeting Name", "Meeting Circuit Shortname"]
    mock_meeting = MagicMock()
    mock_meeting.key = 1212
    mock_meeting.officialname = "Bahrain Grand Prix"
    mock_meeting.name = "Bahrain"
    with patch("livef1.api.get_season") as mock_get_season:
        mock_season = MagicMock()
        mock_season.meetings = [mock_meeting]
        mock_season.meetings_table = pd.DataFrame({
            "Meeting Key": [1212],
            **{c: ["Bahrain"] for c in required_cols},
        })
        mock_season.season_table = mock_season.meetings_table.copy()
        mock_get_season.return_value = mock_season
        with patch("livef1.api.print_found_model"):
            meeting = get_meeting(2024, meeting_key=1212)
    assert meeting is mock_meeting
    assert meeting.key == 1212


def test_get_meeting_returns_meeting_with_expected_attributes():
    """get_meeting returns an object with key, name, sessions, circuit."""
    required_cols = ["Meeting Offname", "Meeting Name", "Meeting Circuit Shortname"]
    mock_meeting = MagicMock()
    mock_meeting.key = 1212
    mock_meeting.name = "Bahrain"
    mock_meeting.officialname = "Bahrain Grand Prix"
    mock_meeting.sessions = {}
    mock_meeting.circuit = MagicMock()
    with patch("livef1.api.get_season") as mock_get_season:
        mock_season = MagicMock()
        mock_season.meetings = [mock_meeting]
        mock_season.meetings_table = pd.DataFrame({
            "Meeting Key": [1212],
            **{c: ["Bahrain"] for c in required_cols},
        })
        mock_season.season_table = mock_season.meetings_table.copy()
        mock_get_season.return_value = mock_season
        with patch("livef1.api.print_found_model"):
            meeting = get_meeting(2024, meeting_key=1212)
    assert hasattr(meeting, "key")
    assert hasattr(meeting, "name")
    assert meeting.key == 1212
    assert meeting.name == "Bahrain"


def test_get_meeting_offname_not_found_raises():
    """get_meeting with unknown meeting_offname raises LiveF1Error."""
    with patch("livef1.api.get_season") as mock_get_season:
        mock_season = MagicMock()
        mock_season.meetings = []
        mock_get_season.return_value = mock_season
        with pytest.raises(LiveF1Error, match="could not be found"):
            get_meeting(2024, meeting_offname="NonExistent Grand Prix")


# ---------- Explicit get_session tests ----------


def test_get_session_by_session_key_explicit():
    """get_session(season, meeting_identifier, session_key=N) returns the session with that key."""
    mock_meeting = MagicMock()
    mock_session = MagicMock()
    mock_session.key = 9465
    mock_session.name = "Race"
    mock_meeting.sessions = {"Race": mock_session}
    mock_meeting.sessions_table = pd.DataFrame({"session_name": ["Race"]}, index=pd.Index([9465], name="session_key"))
    with patch("livef1.api.get_meeting", return_value=mock_meeting):
        with patch("livef1.api.print_found_model"):
            with patch.object(mock_session, "load_session_data"):
                session = get_session(2024, meeting_identifier="Bahrain", session_key=9465)
    assert session is mock_session
    assert session.key == 9465


def test_get_session_returns_session_with_expected_attributes():
    """get_session returns an object with key, name, and load_session_data is invoked."""
    mock_meeting = MagicMock()
    mock_session = MagicMock()
    mock_session.key = 9465
    mock_session.name = "Race"
    mock_meeting.sessions = {"Race": mock_session}
    mock_meeting.sessions_table = pd.DataFrame({"session_name": ["Race"]}, index=pd.Index([9465], name="session_key"))
    with patch("livef1.api.get_meeting", return_value=mock_meeting):
        with patch("livef1.api.print_found_model"):
            with patch.object(mock_session, "load_session_data") as mock_load:
                session = get_session(2024, meeting_identifier="Bahrain", session_identifier="Race")
    assert hasattr(session, "key")
    assert hasattr(session, "name")
    assert session.key == 9465
    mock_load.assert_called_once()


def test_get_session_by_identifier_uses_find_most_similar():
    """get_session(..., session_identifier='Race') uses find_most_similar_vectorized to resolve session."""
    mock_meeting = MagicMock()
    mock_session = MagicMock()
    mock_session.key = 9465
    mock_meeting.sessions = {"Race": mock_session}
    mock_meeting.sessions_table = pd.DataFrame(
        {"session_name": ["Race", "Qualifying"]},
        index=pd.Index([9465, 9464], name="session_key"),
    )
    with patch("livef1.api.get_meeting", return_value=mock_meeting):
        with patch("livef1.api.find_most_similar_vectorized", return_value={"row_index": 0}) as mock_find:
            with patch("livef1.api.print_found_model"):
                with patch.object(mock_session, "load_session_data"):
                    session = get_session(2024, meeting_identifier="Bahrain", session_identifier="Race")
    mock_find.assert_called_once()
    assert session.key == 9465


# ---------- get_meeting + get_session + .generate() in same test ----------


def _dummy_load_single_data_for_generate(dataName, session, stream):
    """Minimal (name, raw, parsed) for generate() bronze tables."""
    raw = {}
    base = [{"SessionKey": 9465, "timestamp": "0", "Utc": "2024-03-02T15:00:00Z"}]
    if dataName == "Position.z":
        parsed = [{"SessionKey": 9465, "timestamp": "0", "Utc": "2024-03-02T15:00:00Z", "DriverNo": "1", "X": 0, "Y": 0, "Z": 0}]
    elif dataName == "CarData.z":
        parsed = [{"SessionKey": 9465, "timestamp": "0", "Utc": "2024-03-02T15:00:00Z", "DriverNo": "1", "Speed": 100}]
    elif dataName in ("Session_Data", "SessionData"):
        parsed = [{"SessionKey": 9465, "SessionStatus": "Started", "Utc": "2024-03-02T15:00:00Z"}]
    elif dataName == "SessionStatus":
        parsed = [{"SessionKey": 9465, "timestamp": "0", "status": "Started", "Utc": "2024-03-02T15:00:00Z"}]
    elif dataName == "TimingData":
        parsed = [{"SessionKey": 9465, "timestamp": "0", "DriverNo": "1", "NumberOfLaps": 1, "LastLapTime_Value": None}]
    elif dataName == "RaceControlMessages":
        parsed = [{"SessionKey": 9465, "timestamp": "0", "Category": "Other", "Message": "Test"}]
    elif dataName == "TyreStintSeries":
        parsed = [{"session_key": 9465, "timestamp": "0", "DriverNo": "1", "Compound": "SOFT", "TotalLaps": 0}]
    elif dataName == "TrackStatus":
        parsed = [{"timestamp": "0", "Status": "1", "Message": "Green"}]
    else:
        parsed = base
    return dataName, raw, parsed


def test_get_meeting_get_session_and_generate_explicit(season_data):
    """Explicitly call get_meeting, get_session, then session.generate() in the same test."""
    index_feeds = {
        "Feeds": {
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
    }

    def mock_circuit_get(url, **kwargs):
        r = MagicMock()
        r.status_code = 200
        if "starting_coordinates" in url or "START_COORDINATES" in str(url):
            r.json.return_value = {"Sakhir": {"start_coordinates": [100.0, 50.0], "start_direction": [1.0, 1.0]}}
        elif "api/v1/circuits" in url:
            r.json.return_value = {"1": {"name": "Sakhir", "circuitKey": 3, "years": [2024]}} if "/circuits/" not in url else {"corners": []}
        else:
            r.json.return_value = {}
        return r

    with patch("livef1.api.download_data", return_value=season_data):
        with patch("livef1.models.season.download_data", return_value=season_data):
            with patch("livef1.models.circuit.requests.get", side_effect=mock_circuit_get):
                with patch("livef1.api.find_most_similar_vectorized", return_value={"row_index": 0}):
                    with patch("livef1.api.print_found_model"):
                        season = get_season(2024)
    assert season is not None
    assert len(season.meetings) >= 1

    with patch("livef1.api.get_season", return_value=season):
        with patch("livef1.api.find_most_similar_vectorized", return_value={"row_index": 0}):
            with patch("livef1.api.print_found_model"):
                meeting = get_meeting(2024, meeting_identifier="Bahrain")
    assert meeting is not None
    assert hasattr(meeting, "sessions")

    session_obj = next((s for s in meeting.sessions.values() if s.key == 9465), list(meeting.sessions.values())[0])

    with patch("livef1.models.session.livetimingF1_request", return_value=index_feeds):
        with patch("livef1.models.session.livetimingF1_getdata", return_value={"1": {"RacingNumber": "1", "Tla": "VER", "FirstName": "Max", "LastName": "Verstappen"}}):
            session_obj.load_session_data()

    def mock_load_circuit_data():
        if not hasattr(session_obj.meeting.circuit, "track_regions"):
            session_obj.meeting.circuit._raw_circuit_data = {"corners": []}
            session_obj.meeting.circuit.track_regions = pd.DataFrame({"name": ["T1"], "corner_start": [0], "corner_end": [100]})
        session_obj.data_lake.create_bronze_table(
            table_name="track_regions",
            raw_data=getattr(session_obj.meeting.circuit, "_raw_circuit_data", {}),
            parsed_data=session_obj.meeting.circuit.track_regions,
        )

    with patch.object(session_obj, "_load_circuit_data", side_effect=mock_load_circuit_data):
        with patch("livef1.models.session.load_single_data", side_effect=_dummy_load_single_data_for_generate):
            session_obj.generate(silver=True, gold=False)

    assert session_obj.first_datetime is not None
    assert session_obj.session_start_datetime is not None
    assert session_obj.data_lake._check_circular_dependencies() is True
    assert "laps" in session_obj.data_lake.metadata or "raceControlMessages" in session_obj.data_lake.metadata
