"""Tests for livef1.utils.constants."""
import pytest
from livef1.utils import constants


def test_base_url():
    assert constants.BASE_URL == "https://livetiming.formula1.com"


def test_static_endpoint():
    assert constants.STATIC_ENDPOINT == "/static/"


def test_silver_session_tables():
    assert constants.SILVER_SESSION_TABLES == ["laps", "carTelemetry", "raceControlMessages"]


def test_table_generation_functions():
    expected = {
        "laps": "generate_laps_table",
        "carTelemetry": "generate_car_telemetry_table",
        "raceControlMessages": "generate_race_control_messages_table",
    }
    assert constants.TABLE_GENERATION_FUNCTIONS == expected


def test_table_requirements():
    assert "laps" in constants.TABLE_REQUIREMENTS
    assert "carTelemetry" in constants.TABLE_REQUIREMENTS
    assert "raceControlMessages" in constants.TABLE_REQUIREMENTS
    assert "TimingData" in constants.TABLE_REQUIREMENTS["laps"]
    assert "CarData.z" in constants.TABLE_REQUIREMENTS["carTelemetry"]


def test_topics_map_has_expected_keys():
    required_topics = ["SessionInfo", "TrackStatus", "TimingData", "DriverList", "CarData.z", "Position.z", "RaceControlMessages"]
    for topic in required_topics:
        assert topic in constants.TOPICS_MAP, f"Missing topic: {topic}"


def test_topics_map_structure():
    for topic, info in constants.TOPICS_MAP.items():
        assert "key" in info
        assert "description" in info
        assert "default_is_stream" in info


def test_query_stopwords():
    assert "formula" in constants.QUERY_STOPWORDS
    assert "1" in constants.QUERY_STOPWORDS
    assert "grand" in constants.QUERY_STOPWORDS
    assert "prix" in constants.QUERY_STOPWORDS


def test_sessions_column_map():
    assert "season_year" in constants.SESSIONS_COLUMN_MAP
    assert constants.SESSIONS_COLUMN_MAP["season_year"] == "Season Year"


def test_silver_laps_col_order_contains_expected():
    assert "SessionKey" in constants.silver_laps_col_order
    assert "DriverNo" in constants.silver_laps_col_order
    assert "LapNo" in constants.silver_laps_col_order
    assert "LapTime" in constants.silver_laps_col_order


def test_silver_cartel_col_order_contains_expected():
    assert "SessionKey" in constants.silver_cartel_col_order
    assert "Speed" in constants.silver_cartel_col_order
    assert "timestamp" in constants.silver_cartel_col_order


def test_penalty_types():
    assert "TIME PENALTY" in constants.penalty_types
    assert "DRIVE THROUGH PENALTY" in constants.penalty_types
