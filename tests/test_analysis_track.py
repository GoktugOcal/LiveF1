"""Unit tests for livef1.analysis track functions."""
import numpy as np
import pandas as pd
import pytest

from livef1 import analysis
from _analysis_data import make_laps, make_track_status, make_lap_telemetry, SC_START, SC_END


def test_track_events_safety_car_window():
    first = pd.Timestamp("2024-03-09T17:00:00Z")
    events = analysis.track_events(make_track_status(), make_laps(), first_datetime=first)
    assert len(events) == 1
    sc = events.iloc[0]
    assert sc["Event"] == "SC"
    assert sc["StartTime"] == pd.Timedelta(seconds=SC_START)
    assert sc["EndTime"] == pd.Timedelta(seconds=SC_END)
    assert (sc["StartLap"], sc["EndLap"]) == (4, 6)
    assert sc["Duration"] == pd.Timedelta(seconds=SC_END - SC_START)
    assert sc["StartDate"] == first + pd.Timedelta(seconds=SC_START)


def test_track_events_vsc_red_and_open_window():
    ts = pd.DataFrame({
        "timestamp": pd.to_timedelta([0, 100, 150, 200, 300, 400, 500], unit="s"),
        "Status": ["1", "6", "7", "1", "4", "5", "1"],
    })
    ts2 = pd.concat([ts, pd.DataFrame({"timestamp": [pd.Timedelta(seconds=600)], "Status": ["5"]})])
    events = analysis.track_events(ts2)
    assert events["Event"].tolist() == ["VSC", "SC", "RED", "RED"]
    # VSC ending ("7") stays in the VSC window
    assert events.iloc[0]["EndTime"] == pd.Timedelta(seconds=200)
    # SC turning into a red flag ends the SC window when the red flag starts
    assert events.iloc[1]["EndTime"] == events.iloc[2]["StartTime"] == pd.Timedelta(seconds=400)
    # Still open at the end of the data
    assert pd.isna(events.iloc[3]["EndTime"])
    assert events["StartLap"].isna().all()


def test_track_events_by_type_matches_legacy_shape():
    events = analysis.track_events(make_track_status(), make_laps())
    assert analysis.track_events_by_type(events) == {"red": [], "virtual_sc": [], "sc": [(4, 6)]}


def test_track_events_empty():
    assert len(analysis.track_events(pd.DataFrame({"timestamp": [], "Status": []}))) == 0
    assert len(analysis.track_events(None)) == 0


def test_corners_table():
    raw = [
        {"number": 2, "letter": "", "length": 4000, "angle": 90.0, "trackPosition": {"x": 10.0, "y": 20.0}},
        {"number": 1, "letter": "a", "length": 1500, "angle": -45.0, "trackPosition": {"x": 1.0, "y": 2.0}},
    ]
    corners = analysis.corners_table(raw)
    assert corners.columns.tolist() == ["Number", "Letter", "Name", "Distance", "X", "Y", "Angle"]
    assert corners["Name"].tolist() == ["T1a", "T2"]
    assert corners["Distance"].tolist() == [150.0, 400.0]
    assert corners["X"].tolist() == [1.0, 10.0]
    assert len(analysis.corners_table([])) == 0


def test_rotate_xy_and_circuit():
    df = pd.DataFrame({"X": [1.0, 0.0], "Y": [0.0, 2.0], "Angle": [0.0, 30.0]})
    out = analysis.rotate_xy(df, 90, angle="Angle")
    assert out["X"].tolist() == pytest.approx([0.0, -2.0])
    assert out["Y"].tolist() == pytest.approx([1.0, 0.0])
    assert out["Angle"].tolist() == [90.0, 120.0]
    assert df["X"].tolist() == [1.0, 0.0]  # input untouched
    tel, corners = analysis.rotate_circuit(df[["X", "Y"]], df, 180)
    assert tel["X"].tolist() == pytest.approx([-1.0, 0.0])
    assert corners["Angle"].tolist() == [180.0, 210.0]
    pd.testing.assert_frame_equal(analysis.rotate_xy(df, 0), df)


REGIONS = pd.DataFrame({
    "name": ["S0", "T1", "S1"],
    "corner_start": [50.0, 100.0, 200.0],
    "corner_end": [100.0, 200.0, 50.0],  # S1 wraps past the line
})


def _two_driver_laps():
    a = make_lap_telemetry("1", 5, 100.0, [(1.0, 36.0, 100, 0)] * 100)   # 10 m/s
    b = make_lap_telemetry("16", 7, 300.0, [(1.0, 32.4, 100, 0)] * 100)  # 9 m/s
    return pd.concat([a, b], ignore_index=True)


def test_assign_track_regions_with_wrap():
    tel = pd.DataFrame({"Distance": [0.0, 60.0, 150.0, 500.0]})
    assert analysis.assign_track_regions(tel, REGIONS).tolist() == ["S1", "S0", "T1", "S1"]


def test_track_region_times():
    times = analysis.track_region_times(_two_driver_laps(), REGIONS)
    ver = times[times.DriverNo == "1"].set_index("TrackRegion")["Time"]
    assert ver["T1"] == pytest.approx(10.0)
    assert ver["S0"] == pytest.approx(5.0)
    # wrap: 200 m -> end of lap (990 m) plus line -> 50 m
    assert ver["S1"] == pytest.approx((990 - 200) / 10 + 50 / 10)
    lec = times[times.DriverNo == "16"].set_index("TrackRegion")["Time"]
    assert lec["T1"] == pytest.approx(100 / 9)
    assert set(times["LapNo"]) == {5.0, 7.0}


def test_track_dominance():
    dom = analysis.track_dominance(analysis.track_region_times(_two_driver_laps(), REGIONS))
    assert dom["TrackRegion"].tolist() == ["S0", "T1", "S1"]
    t1 = dom[dom.TrackRegion == "T1"].iloc[0]
    assert t1["DriverNo"] == "1"
    assert t1["GapToSecond"] == pytest.approx(100 / 9 - 10)


def test_gap_between_drivers():
    gap = analysis.gap_between_drivers(_two_driver_laps(), reference_driver="1", step=10)
    lec = gap[gap.DriverNo == "16"].set_index("Distance")
    assert lec.loc[450.0, "Gap"] == pytest.approx(450 / 9 - 450 / 10)
    assert gap[gap.DriverNo == "1"]["Gap"].abs().max() == pytest.approx(0.0)
    assert gap["Distance"].max() <= 891
    # unknown reference driver gives an empty frame
    assert len(analysis.gap_between_drivers(_two_driver_laps(), reference_driver="99", drivers=["16"])) == 0


def test_lap_clock_ignores_backwards_distance():
    lap = make_lap_telemetry("1", 1, 0.0, [(1.0, 36.0, 100, 0)] * 5)
    lap.loc[3, "Distance"] = 5.0  # GPS glitch going backwards
    times = analysis.track_region_times(lap, pd.DataFrame({"name": ["A"], "corner_start": [0.0], "corner_end": [40.0]}))
    assert np.isfinite(times["Time"]).all()
