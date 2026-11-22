"""
The default analysis tables run through Session.generate(): registration, dependency
resolution (silver -> gold -> gold) and the session attributes they set.

Network and livetiming parsing are replaced: the core ``laps`` and ``carTelemetry``
silver tables are registered with synthetic frames and ``TrackStatus`` is put in the
bronze lake directly.
"""
from types import SimpleNamespace
from unittest.mock import patch

import pandas as pd
import pytest

import livef1
from livef1.config import _settings
from livef1.models.session import Session
from livef1.models.circuit import Circuit
from livef1.data_processing.analysis_tables import ANALYSIS_SILVER_TABLES, ANALYSIS_GOLD_TABLES
from _analysis_data import (
    make_laps, make_track_status, make_lap_one_telemetry, make_lap_telemetry, make_drivers, make_meeting_table,
)

FIRST_DATETIME = pd.Timestamp("2024-07-28T12:50:00Z")


def _telemetry():
    lap_one = make_lap_one_telemetry()
    best = []
    for driver_no, lap_no in [("1", 2), ("16", 6), ("44", 2)]:
        samples = [(1.0, 300, 100, 0)] * 6 + [(1.0, 150, 0, 100)] * 2 + [(1.0, 120, 40, 0)] * 2
        best.append(make_lap_telemetry(driver_no, lap_no, 2000.0, samples))
    return pd.concat([lap_one, *best], ignore_index=True)


@pytest.fixture
def session(monkeypatch):
    monkeypatch.setitem(_settings, "dataframe_backend", "pandas")
    s = Session(name="Race")
    s.meeting = SimpleNamespace(name="Belgian Grand Prix", meeting_table=make_meeting_table(), circuit=None)
    s.topic_names_info = {}
    s.drivers = make_drivers()
    s.startingGrid = pd.DataFrame({"No.": [1, 16, 44], "Pos.": [1, 2, 3]})
    s.data_lake.create_bronze_table(
        table_name="TrackStatus",
        raw_data={},
        parsed_data=make_track_status().assign(timestamp=lambda d: d.timestamp.astype(str)),
    )
    laps, tel = make_laps(), _telemetry()
    s.create_silver_table("laps", [])(lambda: laps.copy())
    s.create_silver_table("carTelemetry", [])(lambda: tel.copy())
    return s


_original_get_data = Session.get_data


def _get_data_without_downloads(self, dataNames, level="bronze", **kwargs):
    # generate() downloads the bronze topics it needs as one list; the test has them already
    if level == "bronze" and isinstance(dataNames, list):
        return {}
    return _original_get_data(self, dataNames, level=level, **kwargs)


def _generate(session, **kwargs):
    with patch("livef1.models.session.SILVER_SESSION_TABLES", []), \
         patch.object(Session, "_load_circuit_data"), \
         patch.object(Session, "load_session_results"), \
         patch.object(Session, "get_data", _get_data_without_downloads), \
         patch.object(Session, "_get_first_datetime", return_value=FIRST_DATETIME), \
         patch.object(Session, "_get_session_start_datetime", return_value=FIRST_DATETIME):
        session.generate(**kwargs)


def test_new_session_has_table_attributes_set_to_none():
    s = Session()
    for name in list(ANALYSIS_SILVER_TABLES) + list(ANALYSIS_GOLD_TABLES):
        assert getattr(s, name) is None
    # session.drivers keeps its own meaning (a dict of Driver objects)
    assert "drivers" not in ANALYSIS_SILVER_TABLES


def test_generate_gold_resolves_dependencies(session):
    _generate(session, gold=True, tables=["DriveCharacter"])
    # DriveCharacter -> FastestLaps -> ValidLaps -> enrichedLaps -> laps (+ TrackStatus), driverInfo, carTelemetry
    for name in ["DriveCharacter", "FastestLaps", "ValidLaps", "enrichedLaps", "driverInfo"]:
        assert isinstance(getattr(session, name), pd.DataFrame), name
    # Not requested and not needed
    assert session.LapOneStart is None
    assert session.trackEvents is None
    assert session.DriveCharacter["DriverNo"].tolist() == ["1", "16", "44"]
    assert session.DriveCharacter["FullThrottlePct"].tolist() == pytest.approx([600 / 9] * 3)
    assert session.FastestLaps["LapNo"].tolist() == [2, 6, 2]


def test_generate_all_default_tables(session):
    _generate(session, silver=True, gold=True)
    s = session
    assert s.driverInfo["Tla"].tolist() == ["VER", "LEC", "HAM"]
    assert s.enrichedLaps["IsValid"].sum() == 9
    assert len(s.ValidLaps) == 8
    assert s.FastestLaps["Tla"].tolist() == ["VER", "LEC", "HAM"]
    assert s.LapTimeStats["DriverNo"].tolist() == ["1", "44", "16"]
    assert s.BestSectors["DriverNo"].tolist() == ["1", "16", "44"]
    assert s.Stints[s.Stints.DriverNo == "44"]["Compound"].tolist() == ["MEDIUM", "HARD"]
    assert s.FuelCorrectedLaps["FuelCorrection"].max() == pd.Timedelta(seconds=5 * 0.047)
    assert s.LapOneStart["TimeTo100kmh"].tolist() == pytest.approx([10.2, 12.8, 8.25])
    assert "Position_1000m" in s.LapOneStart.columns
    ev = s.trackEvents.iloc[0]
    assert (ev["Event"], ev["StartLap"], ev["EndLap"]) == ("SC", 4, 6)
    assert ev["StartDate"] == FIRST_DATETIME + pd.Timedelta(seconds=900)
    assert s.sessionSchedule["StartUtc"].iloc[-1] == pd.Timestamp("2024-07-28 13:00", tz="UTC")
    for name in list(ANALYSIS_SILVER_TABLES) + list(ANALYSIS_GOLD_TABLES):
        assert s.data_lake.metadata[name]["generated"], name
    # session.drivers is untouched
    assert s.drivers["1"].Tla == "VER"


def test_configure_changes_table_defaults(session, monkeypatch):
    monkeypatch.setitem(_settings, "fuel_correction_per_lap", None)
    monkeypatch.setitem(_settings, "lap_one_distances", None)
    livef1.configure(fuel_correction_per_lap=0.1, lap_one_distances=[50, 150.5])
    _generate(session, gold=True, tables=["FuelCorrectedLaps", "LapOneStart"])
    assert session.FuelCorrectedLaps["FuelCorrection"].max() == pd.Timedelta(seconds=0.5)
    assert {"Position_50m", "Speed_150.5m"} <= set(session.LapOneStart.columns)


def test_configure_rejects_empty_distances():
    with pytest.raises(ValueError):
        livef1.configure(lap_one_distances=[])


def test_user_table_with_same_name_is_kept(session):
    session.create_gold_table("FastestLaps", ["laps"])(lambda laps: laps.head(1))
    _generate(session, gold=True, tables=["FastestLaps"])
    assert len(session.FastestLaps) == 1


def test_polars_backend_skips_analysis_tables(monkeypatch):
    pytest.importorskip("polars")
    monkeypatch.setitem(_settings, "dataframe_backend", "polars")
    s = Session()
    s._register_analysis_tables("gold", ANALYSIS_GOLD_TABLES)
    assert not any(name in s.data_lake.metadata for name in ANALYSIS_GOLD_TABLES)


def test_get_lap_telemetry(session):
    assert session.get_lap_telemetry([("1", 2)]) is None  # not generated yet
    _generate(session, silver=True, tables=["carTelemetry"])
    tel = session.get_lap_telemetry([("1", 2), (16, 6.0)])
    assert set(zip(tel.DriverNo, tel.LapNo)) == {("1", 2.0), ("16", 6.0)}
    assert len(session.get_lap_telemetry(pd.DataFrame({"DriverNo": ["44"], "LapNo": [2]}))) == 10


RAW_CIRCUIT = {
    "corners": [
        {"number": 1, "letter": "", "length": 2000, "angle": 10.0, "trackPosition": {"x": 5.0, "y": 6.0}},
        {"number": 2, "letter": "", "length": 6000, "angle": 20.0, "trackPosition": {"x": 7.0, "y": 8.0}},
    ]
}


def test_circuit_corners_and_track_regions_load_lazily():
    circuit = Circuit(key="7", short_name="Spa")
    calls = []

    def fake_load(self):
        calls.append(1)
        self.track_regions = pd.DataFrame({"name": ["T1"], "corner_start": [150.0], "corner_end": [250.0]})
        self._raw_circuit_data = RAW_CIRCUIT

    with patch.object(Circuit, "_load_circuit_data", fake_load):
        assert not circuit.is_circuit_data_loaded
        corners = circuit.corners
        assert corners["Name"].tolist() == ["T1", "T2"]
        assert corners["Distance"].tolist() == [200.0, 600.0]
        assert corners["Angle"].tolist() == [10.0, 20.0]
        assert circuit.track_regions["name"].tolist() == ["T1"]
        circuit.load_circuit_data()
        assert len(calls) == 1
        circuit.load_circuit_data(force=True)
        assert len(calls) == 2


def test_circuit_track_regions_setter_skips_loading():
    circuit = Circuit(key="7", short_name="Spa")
    circuit.track_regions = pd.DataFrame({"name": ["S0"]})
    with patch.object(Circuit, "_load_circuit_data", side_effect=AssertionError("should not load")):
        assert circuit.track_regions["name"].tolist() == ["S0"]


# --- what generate() logs ---------------------------------------------------

import logging

from livef1.utils import logger as logger_module


@pytest.fixture
def records():
    handler = logging.Handler()
    handler.records = []
    handler.emit = handler.records.append
    logger_module.logger.addHandler(handler)
    yield handler.records
    logger_module.logger.removeHandler(handler)
    logger_module.reset_logging()


def _messages(records, level):
    return [r.getMessage() for r in records if r.levelno == level]


def test_generate_logs_a_few_summary_lines(session, records):
    livef1.configure(log_level="DEBUG")
    _generate(session, gold=True)
    info = _messages(records, logging.INFO)
    assert info == [
        "Generating tables for Belgian Grand Prix · Race",
        *[m for m in info if m.startswith("Silver: 6 tables in ")],
        *[m for m in info if m.startswith("Gold: 8 tables in ")],
        *[m for m in info if m.startswith("Done in ") and m.endswith("(+8 more)")],
    ]
    # Registering a table is detail, and names the right level
    debug = _messages(records, logging.DEBUG)
    assert "Registered gold table 'FastestLaps'." in debug
    assert "Registered silver table 'driverInfo'." in debug
    assert any(m.startswith("Built gold table 'FastestLaps': 3 rows in ") for m in debug)


def test_generate_summary_records_carry_structured_fields(session, records):
    livef1.configure(log_level="DEBUG")
    _generate(session, gold=True, tables=["FastestLaps"])
    built = [r for r in records if getattr(r, "event", None) == "table_generated"]
    assert {r.table for r in built} >= {"laps", "enrichedLaps", "ValidLaps", "FastestLaps"}
    assert all(isinstance(r.rows, int) and isinstance(r.duration_ms, int) for r in built)
    finished = [r for r in records if getattr(r, "event", None) == "generate_finished"]
    assert len(finished) == 1 and "FastestLaps" in finished[0].tables and finished[0].failed == []


def test_failed_table_is_one_error_line_with_traceback_only_at_debug(session, records):
    @session.create_gold_table("Broken", ["laps"])
    def broken(laps):
        return laps["NoSuchColumn"]

    _generate(session, gold=True, tables=["Broken"])
    errors = [r for r in records if r.levelno == logging.ERROR]
    assert len(errors) == 1
    assert errors[0].getMessage().startswith("Could not build gold table 'Broken': KeyError")
    assert 'log_level="DEBUG"' in errors[0].getMessage() and errors[0].exc_info is None
    summary = [r for r in records if getattr(r, "event", None) == "tables_generated" and r.layer == "gold"]
    assert summary[0].levelno == logging.WARNING and summary[0].failed == ["Broken"]

    records.clear()
    livef1.configure(log_level="DEBUG")
    session.data_lake.metadata["Broken"]["generated"] = False
    _generate(session, gold=True, tables=["Broken"])
    errors = [r for r in records if r.levelno == logging.ERROR]
    assert errors[0].exc_info is not None
