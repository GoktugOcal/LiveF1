"""Unit tests for livef1.analysis telemetry and schedule functions."""
import numpy as np
import pandas as pd
import pytest

from livef1 import analysis
from _analysis_data import (
    make_laps, make_lap_one_telemetry, make_lap_telemetry, make_driver_info, make_meeting_table,
)


def test_select_lap_telemetry_matches_types_loosely():
    tel = pd.DataFrame({
        "DriverNo": pd.Categorical(["1", "1", "16", "16", "44"]),
        "LapNo": [5.0, 6.0, 5.0, 7.0, 5.0],
        "Speed": [1, 2, 3, 4, 5],
    })
    out = analysis.select_lap_telemetry(tel, [(1, 5), ("16", 7.0)])
    assert out["Speed"].tolist() == [1, 4]
    pairs = pd.DataFrame({"DriverNo": ["44"], "LapNo": [np.uint8(5)]})
    assert analysis.select_lap_telemetry(tel, pairs)["Speed"].tolist() == [5]
    assert len(analysis.select_lap_telemetry(tel, [])) == 0


def _drive_lap(driver_no, t_start):
    samples = [(1.0, 300, 100, 0)] * 6 + [(1.0, 150, 0, 100)] * 2 + [(1.0, 120, 40, 0)] * 2
    return make_lap_telemetry(driver_no, 3, t_start, samples)


def test_drive_character_per_driver_time_shares():
    # Driver 16's lap starts before driver 1's ends: deltas must not cross drivers
    tel = pd.concat([_drive_lap("1", 100.0), _drive_lap("16", 50.0)], ignore_index=True)
    out = analysis.drive_character(tel, driver_info=make_driver_info())
    assert out["DriverNo"].tolist() == ["1", "16"]
    for _, row in out.iterrows():
        # last sample has no following sample: 9 s counted (6 full, 2 braking, 1 cornering)
        assert row["LapDuration"] == pytest.approx(9.0)
        assert row["FullThrottlePct"] == pytest.approx(600 / 9)
        assert row["HeavyBrakingPct"] == pytest.approx(200 / 9)
        assert row["CorneringPct"] == pytest.approx(100 / 9)
        assert row["LapNo"] == 3
    assert out["Tla"].tolist() == ["VER", "LEC"]


def test_drive_character_full_throttle_wins_over_brake():
    lap = make_lap_telemetry("1", 1, 0.0, [(1.0, 200, 100, 100), (1.0, 200, 100, 100), (1.0, 200, 0, 0)])
    out = analysis.drive_character(lap)
    assert out.iloc[0]["FullThrottlePct"] == pytest.approx(100.0)
    assert out.iloc[0]["HeavyBrakingPct"] == 0


def test_lap_one_start_time_to_speed_and_positions():
    tel = make_lap_one_telemetry()
    # Driver 44 is up to P1 from 250 m on
    tel.loc[(tel.DriverNo == "44") & (tel.Distance >= 250), "Position"] = 1.0
    out = analysis.lap_one_start(tel, make_laps(), grid={"1": 1, "16": 2, "44": 3}, distances=(100, 250), driver_info=make_driver_info())
    assert out["DriverNo"].tolist() == ["1", "16", "44"]
    assert out["GridPosition"].tolist() == [1, 2, 3]
    # speed = (t - start - reaction) * accel  ->  time to 100 km/h = reaction + 100 / accel
    assert out["TimeTo100kmh"].tolist() == pytest.approx([0.2 + 10.0, 0.3 + 12.5, 0.25 + 8.0])
    ham = out[out.DriverNo == "44"].iloc[0]
    assert ham["Position_100m"] == 3
    assert ham["PositionsGained_100m"] == 0
    assert ham["Position_250m"] == 1
    assert ham["PositionsGained_250m"] == 2
    assert ham["Speed_250m"] > ham["Speed_100m"] > 0
    assert out["Tla"].tolist() == ["VER", "LEC", "HAM"]


def test_lap_one_start_grid_from_starting_grid_table_and_fallback():
    tel = make_lap_one_telemetry()
    grid = pd.DataFrame({"No.": [16, 1, 44], "Pos.": ["1", "2", "3"]})
    out = analysis.lap_one_start(tel, make_laps(), grid=grid, distances=[100])
    assert out["DriverNo"].tolist() == ["16", "1", "44"]
    # Without a grid, the first lap-1 timing position is used
    out = analysis.lap_one_start(tel, None, distances=[100])
    assert out["GridPosition"].tolist() == [1, 2, 3]
    assert "Position_100m" in out.columns


def test_lap_one_start_no_lap_one():
    tel = make_lap_one_telemetry().assign(LapNo=2.0)
    out = analysis.lap_one_start(tel, distances=[100])
    assert len(out) == 0
    assert "TimeTo100kmh" in out.columns


@pytest.mark.parametrize("text, hours", [
    ("02:00:00", 2), ("-05:00:00", -5), ("+03:00", 3), ("+0530", 5.5), ("03:00", 3),
])
def test_parse_gmt_offset(text, hours):
    assert analysis.parse_gmt_offset(text) == pd.Timedelta(hours=hours)


def test_parse_gmt_offset_invalid():
    assert pd.isna(analysis.parse_gmt_offset(None))
    assert pd.isna(analysis.parse_gmt_offset("soon"))


def test_session_schedule_local_and_utc():
    sched = analysis.session_schedule(make_meeting_table())
    assert sched["SessionName"].tolist() == ["Practice 1", "Qualifying", "Race"]
    race = sched.iloc[2]
    assert race["StartLocal"] == pd.Timestamp("2024-07-28 15:00:00")
    assert race["StartUtc"] == pd.Timestamp("2024-07-28 13:00:00", tz="UTC")
    assert race["EndUtc"] == pd.Timestamp("2024-07-28 15:00:00", tz="UTC")
    assert race["GmtOffset"] == pd.Timedelta(hours=2)
    assert race["SessionType"] == "Race"
    assert race["MeetingName"] == "Belgian Grand Prix"


def test_session_schedule_with_aware_dates():
    table = pd.DataFrame({
        "session_key": [1], "session_name": ["Race"],
        "session_startDate": ["2024-03-02T15:00:00Z"], "session_endDate": [None], "gmtoffset": ["+03:00"],
    })
    row = analysis.session_schedule(table).iloc[0]
    assert row["StartUtc"] == pd.Timestamp("2024-03-02 15:00", tz="UTC")
    assert row["StartLocal"] == pd.Timestamp("2024-03-02 18:00")
    assert pd.isna(row["EndUtc"])


def test_session_schedule_empty():
    assert len(analysis.session_schedule(None)) == 0
