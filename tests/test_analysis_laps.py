"""Unit tests for livef1.analysis lap functions on a small synthetic race."""
import pandas as pd
import pytest

from livef1 import analysis
from _analysis_data import make_laps, make_track_status, make_driver_info, make_drivers, FakeDriver


def _by(df, driver_no, lap_no, col):
    return df[(df.DriverNo == driver_no) & (df.LapNo == lap_no)][col].iloc[0]


@pytest.fixture
def enriched():
    return analysis.enrich_laps(make_laps(), make_track_status())


def test_lap_track_status_includes_status_in_force_at_lap_start(enriched):
    expected = {
        "1": ["1", "1", "1", "1,4", "4", "1,4"],
        "16": ["1", "1", "1,4", "4", "1,4", "1"],
        "44": ["1", "1", "1", "1,4", "1,4", "1"],
    }
    for driver_no, statuses in expected.items():
        got = enriched[enriched.DriverNo == driver_no].sort_values("LapNo")["LapTrackStatus"].tolist()
        assert got == statuses, driver_no
    # The silver column reads lap 5 of driver 1 (fully behind the safety car) as green
    assert _by(enriched, "1", 5, "TrackStatus") == "1"
    assert _by(enriched, "1", 5, "IsGreen") == False  # noqa: E712


def test_lap_track_status_without_track_status_falls_back_to_silver_column():
    laps = analysis.enrich_laps(make_laps(), None)
    assert laps["LapTrackStatus"].tolist() == laps["TrackStatus"].tolist()


def test_is_green_rules():
    assert analysis.is_green(["1", "1,2", "2", "1,4", "4", None, ""]).tolist() == [True, True, False, False, False, False, False]


def test_enrich_laps_stint_and_seconds(enriched):
    stints_44 = enriched[enriched.DriverNo == "44"].sort_values("LapNo")["Stint"].tolist()
    assert stints_44 == [1, 1, 1, 2, 2, 2]
    assert set(enriched[enriched.DriverNo == "1"]["Stint"]) == {1}
    assert _by(enriched, "16", 2, "LapTimeSeconds") == pytest.approx(120.0)


def test_enrich_laps_is_valid(enriched):
    valid = {d: sorted(enriched[(enriched.DriverNo == d) & enriched.IsValid]["LapNo"].tolist()) for d in ["1", "16", "44"]}
    assert valid == {"1": [1, 2, 3], "16": [1, 2, 6], "44": [1, 2, 6]}
    # pit in, pit out and deleted laps are never valid
    assert not _by(enriched, "44", 3, "IsValid")
    assert not _by(enriched, "1", 6, "IsValid")


def test_enrich_laps_does_not_modify_input():
    laps = make_laps()
    before = laps.copy()
    analysis.enrich_laps(laps, make_track_status())
    pd.testing.assert_frame_equal(laps, before)


def test_enrich_laps_lap_without_time_is_invalid():
    laps = make_laps()
    laps.loc[(laps.DriverNo == "1") & (laps.LapNo == 2), "LapTime"] = pd.NaT
    out = analysis.enrich_laps(laps, make_track_status())
    assert not _by(out, "1", 2, "IsValid")


def test_remove_outliers_high_side_only():
    df = pd.DataFrame({"LapTime": pd.to_timedelta([80, 90, 90.5, 91, 91.5, 92, 150], unit="s")})
    kept = analysis.remove_outliers(df, "LapTime")
    assert kept["LapTime"].dt.total_seconds().tolist() == [80, 90, 90.5, 91, 91.5, 92]


def test_valid_laps_drops_outlier_and_sorts(enriched):
    valid = analysis.valid_laps(enriched)
    assert len(valid) == 8
    assert 120.0 not in valid["LapTimeSeconds"].tolist()
    assert valid["LapTime"].is_monotonic_increasing
    # Also accepts the raw silver laps table
    assert len(analysis.valid_laps(make_laps(), track_status=make_track_status())) == 8
    assert len(analysis.valid_laps(enriched, iqr_factor=None)) == 9


def test_fastest_laps(enriched):
    fastest = analysis.fastest_laps(analysis.valid_laps(enriched), make_driver_info())
    assert fastest["DriverNo"].tolist() == ["1", "16", "44"]
    assert fastest["LapNo"].tolist() == [2, 6, 2]
    assert fastest["Position"].tolist() == [1, 2, 3]
    assert fastest["GapToFastestSeconds"].tolist() == pytest.approx([0.0, 0.9, 1.0])
    assert fastest["Tla"].tolist() == ["VER", "LEC", "HAM"]
    assert fastest["TeamColour"].tolist() == ["#3671C6", "#E8002D", "#27F4D2"]


def test_fastest_laps_empty():
    out = analysis.fastest_laps(make_laps().iloc[0:0])
    assert len(out) == 0
    assert {"DriverNo", "LapTime", "GapToFastest", "Tla"} <= set(out.columns)


def test_laptime_stats(enriched):
    stats = analysis.laptime_stats(analysis.valid_laps(enriched), make_driver_info())
    assert stats["DriverNo"].tolist() == ["1", "44", "16"]
    ver = stats.iloc[0]
    assert ver["LapCount"] == 3
    assert ver["LapTimeMin"].total_seconds() == pytest.approx(90.0)
    assert ver["LapTimeQ1"].total_seconds() == pytest.approx(90.25)
    assert ver["LapTimeMean"].total_seconds() == pytest.approx(275.5 / 3)
    assert ver["LapTimeQ3"].total_seconds() == pytest.approx(92.75)
    assert ver["LapTimeMax"].total_seconds() == pytest.approx(95.0)
    assert stats["MeanGapToLeaderSeconds"].tolist() == pytest.approx([0.0, 1.0, 93.2 - 275.5 / 3])
    assert stats["MeanGapToLeader"].iloc[1].total_seconds() == pytest.approx(1.0)


def test_best_sectors(enriched):
    best = analysis.best_sectors(make_laps(), make_driver_info())
    assert best["DriverNo"].tolist() == ["1", "16", "44"]
    lec = best[best.DriverNo == "16"].iloc[0]
    assert lec["BestSector1"].total_seconds() == pytest.approx(26.5)
    assert lec["TheoreticalBest"].total_seconds() == pytest.approx(26.5 + 36.32 + 27.24)
    ver = best[best.DriverNo == "1"].iloc[0]
    # Driver 1's deleted 89.0 lap does not count
    assert ver["BestSector1"].total_seconds() == pytest.approx(27.0)
    assert ver["Sector1Gap"] == pytest.approx(0.5)
    assert best["TheoreticalBestGap"].tolist() == pytest.approx([0.0, 0.06, 1.0])


def test_stints(enriched):
    st = analysis.stints(enriched, make_driver_info())
    ham = st[st.DriverNo == "44"].sort_values("Stint")
    assert ham["Compound"].tolist() == ["MEDIUM", "HARD"]
    assert ham["StartLap"].tolist() == [1, 4]
    assert ham["EndLap"].tolist() == [3, 6]
    assert ham["Laps"].tolist() == [3, 3]
    assert ham["StartTyreAge"].tolist() == [4, 1]
    assert ham["ValidLaps"].tolist() == [2, 1]
    assert ham["MeanLapTimeSeconds"].tolist() == pytest.approx([93.5, 91.5])
    assert ham["Tla"].iloc[0] == "HAM"
    assert len(st[st.DriverNo == "1"]) == 1


def test_fuel_corrected_laps(enriched):
    out = analysis.fuel_corrected_laps(enriched, correction_per_lap=0.05)
    lap6 = out[(out.DriverNo == "16") & (out.LapNo == 6)].iloc[0]
    assert lap6["FuelCorrection"].total_seconds() == pytest.approx(0.25)
    assert lap6["FuelCorrectedLapTimeSeconds"] == pytest.approx(90.9 + 0.25)
    lap1 = out[(out.DriverNo == "16") & (out.LapNo == 1)].iloc[0]
    assert lap1["FuelCorrection"].total_seconds() == 0
    assert len(out) == len(enriched)


def test_driver_info_columns_and_colour():
    drivers = make_drivers()
    drivers["99"] = FakeDriver("99", None, "Test", "Driver", None, None, FullName="")
    info = analysis.driver_info(drivers)
    assert info.columns.tolist() == ["DriverNo", "Tla", "FullName", "FirstName", "LastName", "TeamName", "TeamColour"]
    assert info["DriverNo"].tolist() == ["1", "16", "44", "99"]
    assert info["TeamColour"].tolist()[:3] == ["#3671C6", "#E8002D", "#27F4D2"]
    assert pd.isna(info["TeamColour"].iloc[3])
    assert info[info.DriverNo == "99"]["FullName"].iloc[0] == "Test Driver"
    assert len(analysis.driver_info({})) == 0


def test_to_timedelta_parses_strings_and_numbers():
    from livef1.analysis._utils import to_timedelta
    got = to_timedelta(pd.Series(["1:32.456", "32.5", "", None, "bad"])).dt.total_seconds().tolist()
    assert got[:2] == pytest.approx([92.456, 32.5])
    assert all(pd.isna(v) for v in got[2:])
    assert to_timedelta(pd.Series([90.5])).iloc[0].total_seconds() == 90.5
