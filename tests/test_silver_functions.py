"""Tests for livef1.data_processing.silver_functions."""
import pytest
import pandas as pd
from livef1.data_processing.silver_functions import (
    add_distance_to_lap,
    add_track_status,
    add_track_status_telemetry,
    add_lineposition,
    assign_regions,
    generate_race_control_messages_table,
)
from unittest.mock import MagicMock


def test_add_distance_to_lap(sample_laps_df):
    result = add_distance_to_lap(sample_laps_df, 100.0, 50.0, 1.0, 1.0)
    assert "Distance" in result.columns
    assert result["Distance"].notna().any() or len(result) == 0


def test_add_distance_to_lap_empty():
    empty = pd.DataFrame(columns=["timestamp", "Speed", "X", "Y"])
    result = add_distance_to_lap(empty, 0, 0, 1, 1)
    assert "Distance" not in result.columns or result.empty


def test_add_track_status(sample_laps_df, sample_track_status_df):
    laps = sample_laps_df.copy()
    laps["LapStartTime"] = pd.to_timedelta(laps["LapStartTime"])
    result = add_track_status(laps, sample_track_status_df)
    assert "TrackStatus" in result.columns


def test_add_track_status_telemetry(sample_telemetry_df, sample_track_status_df):
    result = add_track_status_telemetry(sample_telemetry_df.copy(), sample_track_status_df)
    assert "TrackStatus" in result.columns
    assert "SessionKey" in result.columns


def test_add_lineposition(sample_telemetry_df, sample_tmg_df):
    tel = sample_telemetry_df.copy()
    result = add_lineposition(tel, sample_tmg_df)
    assert "Position" in result.columns


def test_assign_regions():
    tel_cor = pd.DataFrame({"Distance": [0, 500, 1000, 2000, 5000]})
    df_corners = pd.DataFrame({
        "name": ["S1", "S2", "S3"],
        "corner_start": [0, 1000, 3000],
        "corner_end": [1000, 3000, 6000],
    })
    result = assign_regions(tel_cor, df_corners)
    assert len(result) == len(tel_cor)
    assert result[0] == "S1"
    assert result[2] == "S2"
    assert result[4] == "S3"


def test_assign_regions_wraparound():
    tel_cor = pd.DataFrame({"Distance": [5500, 500]})
    df_corners = pd.DataFrame({
        "name": ["End", "Start"],
        "corner_start": [5000, 0],
        "corner_end": [1000, 5000],
    })
    result = assign_regions(tel_cor, df_corners)
    assert len(result) == 2


def test_generate_race_control_messages_table(mock_session):
    rcm_df = pd.DataFrame({
        "SessionKey": [9465, 9465],
        "timestamp": [pd.Timedelta("1h30m"), pd.Timedelta("1h31m")],
        "Utc": ["2024-03-02T15:30:00Z", "2024-03-02T15:31:00Z"],
        "Category": ["Other", "Flag"],
        "Scope": ["All", "Track"],
        "Status": ["1", "1"],
        "Flag": [None, "YELLOW"],
        "Message": ["RACE CONTROL MESSAGE", "YELLOW FLAG"],
        "Lap": [1, 2],
        "RacingNumber": ["1", None],
    })
    result = generate_race_control_messages_table(mock_session, rcm_df.copy())
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 2
    assert "SessionKey" in result.columns
    assert "Message" in result.columns
    assert "Category" in result.columns
