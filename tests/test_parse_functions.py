"""Tests for livef1.data_processing.parse_functions."""
import pytest
import base64
import zlib
from livef1.data_processing.parse_functions import (
    parse_tyre_stint_series,
    parse_driver_race_info,
    parse_current_tyres,
    parse_driver_list,
    parse_session_data,
    parse_extrapolated_clock,
    parse_timing_data,
    parse_lap_series,
    parse_top_three,
    parse_session_status,
    parse_hearthbeat,
    parse_weather_data,
    parse_tlarcm,
    parse_race_control_messages,
    parse_session_info,
    parse_pit_lane_time,
    parse_pit_stop_series,
    parse_basic,
)


SESSION_KEY = 9465


def test_parse_tyre_stint_series():
    data = [("0", {"Stints": {"1": {"0": {"Compound": "SOFT", "Lap": 1}}}})]
    records = list(parse_tyre_stint_series(data, SESSION_KEY))
    assert len(records) == 1
    assert records[0]["session_key"] == SESSION_KEY
    assert records[0]["DriverNo"] == "1"
    assert records[0]["Compound"] == "SOFT"


def test_parse_driver_race_info():
    data = [("0", {"1": {"Position": "1", "Laps": 50}})]
    records = list(parse_driver_race_info(data, SESSION_KEY))
    assert len(records) == 1
    assert records[0]["session_key"] == SESSION_KEY
    assert records[0]["DriverNo"] == "1"
    assert records[0]["Position"] == "1"


def test_parse_current_tyres():
    data = [("0", {"Tyres": {"1": {"Compound": "SOFT", "Age": 5}}})]
    records = list(parse_current_tyres(data, SESSION_KEY))
    assert len(records) == 1
    assert records[0]["session_key"] == SESSION_KEY
    assert records[0]["DriverNo"] == "1"
    assert records[0]["Compound"] == "SOFT"


def test_parse_driver_list_dict():
    data = {"1": {"RacingNumber": "1", "Tla": "VER"}, "2": {"RacingNumber": "2", "Tla": "NOR"}}
    records = list(parse_driver_list(data, SESSION_KEY))
    assert len(records) == 2
    assert records[0]["RacingNumber"] == "1"
    assert records[1]["Tla"] == "NOR"


def test_parse_driver_list_stream():
    data = [("key", {"1": {"RacingNumber": "1", "Tla": "VER"}})]
    records = list(parse_driver_list(data, SESSION_KEY))
    assert len(records) == 1
    assert records[0]["Tla"] == "VER"


def test_parse_session_data():
    data = [("0", {"1": {"info": {"Status": "Active"}}})]
    records = list(parse_session_data(data, SESSION_KEY))
    assert len(records) == 1
    assert records[0]["session_key"] == SESSION_KEY


def test_parse_extrapolated_clock():
    data = [("0", {"Elapsed": 3600})]
    records = list(parse_extrapolated_clock(data, SESSION_KEY))
    assert len(records) == 1
    assert records[0]["session_key"] == SESSION_KEY
    assert records[0]["timestamp"] == "0"
    assert records[0]["Elapsed"] == 3600


def test_parse_timing_data():
    data = [("0", {"Lines": {"1": {"NumberOfLaps": 50, "LastLapTime": {"Value": 90000}}}})]
    records = list(parse_timing_data(data, SESSION_KEY))
    assert len(records) == 1
    assert records[0]["SessionKey"] == SESSION_KEY
    assert records[0]["DriverNo"] == "1"


def test_parse_timing_data_withheld():
    data = [("0", {"Withheld": ["1"], "Lines": {"2": {"Laps": 1}}})]
    records = list(parse_timing_data(data, SESSION_KEY))
    assert len(records) == 1
    assert records[0]["DriverNo"] == "2"


def test_parse_lap_series_list():
    data = [("0", {"1": {"LapPosition": [1, 2, 3]}})]
    records = list(parse_lap_series(data, SESSION_KEY))
    assert len(records) == 3
    assert all(r["SessionKey"] == SESSION_KEY for r in records)


def test_parse_lap_series_dict():
    data = [("0", {"1": {"LapPosition": {"1": 1, "2": 2}}})]
    records = list(parse_lap_series(data, SESSION_KEY))
    assert len(records) == 2


def test_parse_top_three():
    data = [("0", {"Lines": {"1": {"Position": "1", "Tla": "VER"}}})]
    records = list(parse_top_three(data, SESSION_KEY))
    assert len(records) == 1
    assert records[0]["SessionKey"] == SESSION_KEY
    assert records[0]["DriverAtPosition"] == "1"


def test_parse_top_three_withheld():
    data = [("0", {"Withheld": True})]
    records = list(parse_top_three(data, SESSION_KEY))
    assert len(records) == 0


def test_parse_session_status():
    data = [("0", {"Status": "Started"})]
    records = list(parse_session_status(data, SESSION_KEY))
    assert len(records) == 1
    assert records[0]["status"] == "Started"
    assert records[0]["SessionKey"] == SESSION_KEY


def test_parse_hearthbeat():
    data = [("0", {"Utc": "2024-03-02T15:00:00Z"})]
    records = list(parse_hearthbeat(data, SESSION_KEY))
    assert len(records) == 1
    assert records[0]["utc"] == "2024-03-02T15:00:00Z"


def test_parse_weather_data():
    data = [("0", {"AirTemp": 25, "TrackTemp": 40})]
    records = list(parse_weather_data(data, SESSION_KEY))
    assert len(records) == 1
    assert records[0]["AirTemp"] == 25
    assert records[0]["TrackTemp"] == 40


def test_parse_tlarcm():
    data = [("0", {"Message": "Safety car deployed"})]
    records = list(parse_tlarcm(data, SESSION_KEY))
    assert len(records) == 1
    assert records[0]["Message"] == "Safety car deployed"


def test_parse_race_control_messages_list():
    data = [("0", {"Messages": [{"Category": "Other", "Message": "Test"}]})]
    records = list(parse_race_control_messages(data, SESSION_KEY))
    assert len(records) == 1
    assert records[0]["Category"] == "Other"
    assert records[0]["Message"] == "Test"


def test_parse_race_control_messages_dict():
    data = [("0", {"Messages": {"0": {"Category": "Flag", "Message": "Yellow"}}})]
    records = list(parse_race_control_messages(data, SESSION_KEY))
    assert len(records) == 1
    assert records[0]["Message"] == "Yellow"


def test_parse_session_info():
    data = [("0", {"SessionStatus": "Started", "Key": 9465})]
    records = list(parse_session_info(data, SESSION_KEY))
    assert len(records) == 1
    assert records[0]["SessionKey"] == SESSION_KEY
    assert records[0]["SessionStatus"] == "Started"


def test_parse_pit_lane_time():
    data = [("0", {"PitTimes": {"1": {"Time": 25000}}})]
    records = list(parse_pit_lane_time(data, SESSION_KEY))
    assert len(records) == 1
    assert records[0]["timestamp"] == "0"
    assert records[0]["Time"] == 25000


def test_parse_pit_stop_series_list():
    data = [("0", {"PitTimes": {"1": [{"Timestamp": "2024-03-02T15:30:00Z", "PitStop": {"Duration": 25000}}]}})]
    records = list(parse_pit_stop_series(data, SESSION_KEY))
    assert len(records) == 1
    assert records[0]["Utc"] == "2024-03-02T15:30:00Z"
    assert records[0]["Duration"] == 25000


def test_parse_pit_stop_series_dict():
    data = [("0", {"PitTimes": {"1": {"0": {"Timestamp": "2024-03-02T15:30:00Z", "PitStop": {"Duration": 24000}}}}})]
    records = list(parse_pit_stop_series(data, SESSION_KEY))
    assert len(records) == 1
    assert records[0]["Duration"] == 24000


def test_parse_basic():
    data = [("0", {"key": "value"})]
    records = list(parse_basic(data, SESSION_KEY))
    assert len(records) == 1
    assert records[0]["timestamp"] == "0"
    assert records[0]["key"] == "value"
