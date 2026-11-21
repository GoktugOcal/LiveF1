"""
Lap-level analyses: lap enrichment, valid laps, fastest laps, pace statistics,
best sectors, stints and fuel correction.

All functions take pandas DataFrames shaped like LiveF1's silver ``laps`` table
and return new DataFrames; inputs are never modified.
"""
import numpy as np
import pandas as pd

from ._utils import add_driver_info, driver_key, empty_frame, status_codes, to_seconds, to_timedelta

#: Track status codes of the livetiming ``TrackStatus`` topic.
TRACK_STATUS = {
    "1": "Green",
    "2": "Yellow",
    "4": "SafetyCar",
    "5": "Red",
    "6": "VSCDeployed",
    "7": "VSCEnding",
}

#: Codes a lap may have seen and still count as a green-flag lap (it must include "1").
GREEN_TRACK_STATUS_CODES = frozenset({"1", "2"})

DEFAULT_IQR_FACTOR = 1.5
DEFAULT_FUEL_CORRECTION_PER_LAP = 0.047  # seconds per lap


def lap_track_status(laps, track_status):
    """
    Every track status active during each lap, as a sorted comma-joined string.

    The silver ``laps.TrackStatus`` column lists the status *changes* that
    happened during a lap and falls back to ``"1"`` for a lap without changes, so a
    lap run entirely behind the safety car reads as green there. This function adds
    the status already in force when the lap started.

    Parameters
    ----------
    laps : pandas.DataFrame
        Columns ``DriverNo``, ``LapNo``, ``LapStartTime`` and ``LapTime``
        (lap end is ``LapStartTime + LapTime``, else the driver's next lap start).
    track_status : pandas.DataFrame
        Bronze ``TrackStatus`` topic: ``timestamp`` and ``Status``.

    Returns
    -------
    pandas.Series
        Aligned to ``laps.index``; ``None`` where the lap has no start time.
    """
    result = pd.Series([None] * len(laps), index=laps.index, dtype=object)
    if track_status is None or len(track_status) == 0 or len(laps) == 0:
        return result

    ts = track_status[["timestamp", "Status"]].copy()
    ts["timestamp"] = pd.to_timedelta(ts["timestamp"], errors="coerce")
    ts = ts.dropna(subset=["timestamp"]).sort_values("timestamp", kind="stable")
    ts["Status"] = ts["Status"].astype(str)
    if ts.empty:
        return result
    times = ts["timestamp"].to_numpy()
    codes = ts["Status"].to_numpy()

    start = pd.to_timedelta(laps["LapStartTime"], errors="coerce")
    end = start + to_timedelta(laps["LapTime"])
    next_start = (
        pd.DataFrame({"DriverNo": driver_key(laps["DriverNo"]), "LapNo": laps["LapNo"], "start": start})
        .sort_values(["DriverNo", "LapNo"])
        .groupby("DriverNo")["start"]
        .shift(-1)
    )
    end = end.fillna(next_start.reindex(laps.index))

    for idx, lap_start, lap_end in zip(laps.index, start, end):
        if pd.isna(lap_start):
            continue
        active = set()
        before = np.searchsorted(times, lap_start.to_timedelta64(), side="right") - 1
        if before >= 0:
            active.add(codes[before])
        if not pd.isna(lap_end):
            lo = np.searchsorted(times, lap_start.to_timedelta64(), side="right")
            hi = np.searchsorted(times, lap_end.to_timedelta64(), side="left")
            active.update(codes[lo:hi])
        if not active:
            active.add("1")
        result.at[idx] = ",".join(sorted(active))
    return result


def is_green(track_status_values):
    """True where the lap only saw green or yellow and was green at some point."""
    return pd.Series(track_status_values).map(
        lambda v: (lambda c: bool(c) and c <= GREEN_TRACK_STATUS_CODES and "1" in c)(status_codes(v))
    ).astype(bool)


def enrich_laps(laps, track_status=None):
    """
    Add ``Stint``, ``LapTimeSeconds``, ``LapTrackStatus``, ``IsGreen`` and ``IsValid`` to the laps table.

    - ``Stint``: 1-based stint number per driver, ``NoPits + 1`` (``NoPits`` counts
      pit exits up to and including the lap).
    - ``LapTimeSeconds``: ``LapTime`` in seconds.
    - ``LapTrackStatus``: every status active during the lap (see :func:`lap_track_status`);
      without ``track_status`` it is a copy of ``TrackStatus``.
    - ``IsGreen``: the lap only saw codes ``1``/``2`` and included ``1``.
    - ``IsValid``: green, not an in- or out-lap, not deleted, and has a lap time.
    """
    out = laps.copy()
    if len(out) == 0:
        for col in ["Stint", "LapTimeSeconds", "LapTrackStatus", "IsGreen", "IsValid"]:
            out[col] = pd.Series(dtype=object)
        return out

    out["LapTime"] = to_timedelta(out["LapTime"])
    out["LapTimeSeconds"] = out["LapTime"].dt.total_seconds()

    out = out.sort_values(["DriverNo", "LapNo"], kind="stable")
    if "NoPits" in out.columns:
        no_pits = pd.to_numeric(out["NoPits"], errors="coerce")
        no_pits = no_pits.groupby(driver_key(out["DriverNo"])).ffill().fillna(0)
        out["Stint"] = (no_pits + 1).astype(int)
    else:
        out["Stint"] = 1

    if track_status is not None and len(track_status) and "LapStartTime" in out.columns:
        out["LapTrackStatus"] = lap_track_status(out, track_status)
        if "TrackStatus" in out.columns:
            out["LapTrackStatus"] = out["LapTrackStatus"].fillna(out["TrackStatus"])
    else:
        out["LapTrackStatus"] = out["TrackStatus"] if "TrackStatus" in out.columns else None

    out["IsGreen"] = is_green(out["LapTrackStatus"]).to_numpy()
    pit_in = out["PitIn"].isna() if "PitIn" in out.columns else True
    pit_out = out["PitOut"].isna() if "PitOut" in out.columns else True
    deleted = out["IsDeleted"].fillna(False).astype(bool) if "IsDeleted" in out.columns else False
    out["IsValid"] = (out["IsGreen"] & pit_in & pit_out & ~deleted & out["LapTime"].notna()).astype(bool)
    return out.reset_index(drop=True)


def remove_outliers(laps, column="LapTime", factor=DEFAULT_IQR_FACTOR):
    """Drop rows whose ``column`` is above ``Q3 + factor * IQR`` (high side only)."""
    if len(laps) == 0:
        return laps.copy()
    values = to_seconds(laps[column])
    q1, q3 = values.quantile(0.25), values.quantile(0.75)
    upper = q3 + factor * (q3 - q1)
    return laps[values <= upper].copy()


def valid_laps(laps, iqr_factor=DEFAULT_IQR_FACTOR, track_status=None):
    """
    Valid laps (see :func:`enrich_laps`) without high-side lap time outliers, fastest first.

    The IQR bound is computed over all drivers' valid laps. Pass ``iqr_factor=None``
    to keep the outliers. ``laps`` may be the raw silver table or the output of
    :func:`enrich_laps`.
    """
    if "IsValid" not in laps.columns:
        laps = enrich_laps(laps, track_status)
    valid = laps[laps["IsValid"].astype(bool)].copy()
    valid["LapTime"] = to_timedelta(valid["LapTime"])
    if iqr_factor is not None:
        valid = remove_outliers(valid, "LapTime", iqr_factor)
    return valid.sort_values("LapTime", kind="stable").reset_index(drop=True)


FASTEST_LAPS_COLUMNS = [
    "Position", "DriverNo", "LapNo", "LapTime", "LapTimeSeconds", "GapToFastest", "GapToFastestSeconds",
    "Compound", "TyreAge", "Stint",
]


def fastest_laps(laps, driver_info=None):
    """
    Each driver's fastest lap with the gap to the overall fastest, ordered P1 first.

    ``Position`` is the rank by fastest lap (1 = fastest).
    """
    laps = laps.dropna(subset=["LapTime"]) if len(laps) else laps
    if len(laps) == 0:
        return add_driver_info(empty_frame(FASTEST_LAPS_COLUMNS), driver_info)
    laps = laps.copy()
    laps["LapTime"] = to_timedelta(laps["LapTime"])
    laps["DriverNo"] = driver_key(laps["DriverNo"])
    best = laps.loc[laps.groupby("DriverNo")["LapTime"].idxmin()].sort_values(["LapTime", "LapNo"], kind="stable")
    best = best.reset_index(drop=True)
    best["LapTimeSeconds"] = best["LapTime"].dt.total_seconds()
    best["GapToFastest"] = best["LapTime"] - best["LapTime"].min()
    best["GapToFastestSeconds"] = best["GapToFastest"].dt.total_seconds()
    best["Position"] = np.arange(1, len(best) + 1)
    for col in FASTEST_LAPS_COLUMNS:
        if col not in best.columns:
            best[col] = None
    return add_driver_info(best[FASTEST_LAPS_COLUMNS], driver_info)


LAP_TIME_STATS_COLUMNS = [
    "DriverNo", "LapCount", "LapTimeMin", "LapTimeQ1", "LapTimeMean", "LapTimeQ3", "LapTimeMax",
    "MeanGapToLeader", "MeanGapToLeaderSeconds",
]


def laptime_stats(laps, driver_info=None):
    """
    Per-driver lap time distribution (min, quartiles, mean, max) and mean gap to the fastest mean.

    Rows are ordered by mean lap time. Times are timedeltas; quartiles use linear
    interpolation like ``numpy.quantile``.
    """
    laps = laps.dropna(subset=["LapTime"]) if len(laps) else laps
    if len(laps) == 0:
        return add_driver_info(empty_frame(LAP_TIME_STATS_COLUMNS), driver_info)
    seconds = pd.DataFrame({"DriverNo": driver_key(laps["DriverNo"]).to_numpy(), "t": to_seconds(laps["LapTime"]).to_numpy()})
    grouped = seconds.groupby("DriverNo")["t"]
    stats = pd.DataFrame({
        "LapCount": grouped.count(),
        "LapTimeMin": grouped.min(),
        "LapTimeQ1": grouped.quantile(0.25),
        "LapTimeMean": grouped.mean(),
        "LapTimeQ3": grouped.quantile(0.75),
        "LapTimeMax": grouped.max(),
    }).reset_index()
    stats["MeanGapToLeaderSeconds"] = stats["LapTimeMean"] - stats["LapTimeMean"].min()
    for col in ["LapTimeMin", "LapTimeQ1", "LapTimeMean", "LapTimeQ3", "LapTimeMax"]:
        stats[col] = pd.to_timedelta(stats[col], unit="s")
    stats["MeanGapToLeader"] = pd.to_timedelta(stats["MeanGapToLeaderSeconds"], unit="s")
    stats = stats.sort_values("LapTimeMean", kind="stable").reset_index(drop=True)
    return add_driver_info(stats[LAP_TIME_STATS_COLUMNS], driver_info)


BEST_SECTORS_COLUMNS = [
    "DriverNo",
    "BestSector1", "BestSector2", "BestSector3",
    "Sector1Gap", "Sector2Gap", "Sector3Gap",
    "TheoreticalBest", "TheoreticalBestGap",
]


def best_sectors(laps, driver_info=None):
    """
    Each driver's best sector times from non-deleted laps, gaps to the best of each sector
    (seconds), and the theoretical best lap (sum of the driver's best sectors).

    Rows are ordered by theoretical best lap.
    """
    if "IsDeleted" in laps.columns:
        laps = laps[laps["IsDeleted"].fillna(False).astype(bool) == False]  # noqa: E712
    if len(laps) == 0:
        return add_driver_info(empty_frame(BEST_SECTORS_COLUMNS), driver_info)
    sectors = pd.DataFrame({"DriverNo": driver_key(laps["DriverNo"]).to_numpy()})
    for n in (1, 2, 3):
        sectors[f"BestSector{n}"] = to_timedelta(laps[f"Sector{n}_Time"]).to_numpy()
    best = sectors.groupby("DriverNo")[["BestSector1", "BestSector2", "BestSector3"]].min().reset_index()
    for n in (1, 2, 3):
        col = f"BestSector{n}"
        best[f"Sector{n}Gap"] = (best[col] - best[col].min()).dt.total_seconds()
    best["TheoreticalBest"] = best["BestSector1"] + best["BestSector2"] + best["BestSector3"]
    best["TheoreticalBestGap"] = (best["TheoreticalBest"] - best["TheoreticalBest"].min()).dt.total_seconds()
    best = best.sort_values("TheoreticalBest", kind="stable", na_position="last").reset_index(drop=True)
    return add_driver_info(best[BEST_SECTORS_COLUMNS], driver_info)


STINTS_COLUMNS = [
    "DriverNo", "Stint", "Compound", "StartLap", "EndLap", "Laps", "StartTyreAge",
    "ValidLaps", "MeanLapTime", "MeanLapTimeSeconds",
]


def stints(laps, driver_info=None):
    """
    One row per driver stint: compound, first and last lap, lap count, tyre age at the
    first lap, and mean lap time over the stint's valid laps.

    ``laps`` must have a ``Stint`` column (see :func:`enrich_laps`); ``IsValid`` is
    used for the pace if present, else every lap with a time counts.
    """
    if len(laps) == 0:
        return add_driver_info(empty_frame(STINTS_COLUMNS), driver_info)
    df = laps.copy()
    df["DriverNo"] = driver_key(df["DriverNo"])
    df = df.sort_values(["DriverNo", "LapNo"], kind="stable")
    df["_t"] = to_seconds(df["LapTime"])
    valid = df["IsValid"].astype(bool) if "IsValid" in df.columns else df["_t"].notna()
    df["_valid_t"] = df["_t"].where(valid)

    def first_valid(s):
        s = s.dropna()
        return s.iloc[0] if len(s) else None

    def mode(s):
        s = s.dropna()
        return s.astype(str).mode().iloc[0] if len(s) else None

    grouped = df.groupby(["DriverNo", "Stint"], sort=True)
    out = pd.DataFrame({
        "Compound": grouped["Compound"].agg(mode) if "Compound" in df.columns else None,
        "StartLap": grouped["LapNo"].min(),
        "EndLap": grouped["LapNo"].max(),
        "Laps": grouped["LapNo"].count(),
        "StartTyreAge": grouped["TyreAge"].agg(first_valid) if "TyreAge" in df.columns else None,
        "ValidLaps": grouped["_valid_t"].count(),
        "MeanLapTimeSeconds": grouped["_valid_t"].mean(),
    }).reset_index()
    out["MeanLapTime"] = pd.to_timedelta(out["MeanLapTimeSeconds"], unit="s")
    return add_driver_info(out[STINTS_COLUMNS], driver_info)


def fuel_corrected_laps(laps, correction_per_lap=DEFAULT_FUEL_CORRECTION_PER_LAP):
    """
    Add fuel-corrected lap times, normalised to the start-of-race fuel load.

    ``FuelCorrection = (LapNo - 1) * correction_per_lap`` seconds is added to
    ``LapTime``: later laps are run lighter, so they get slower corrected times.
    Adds ``FuelCorrection`` (timedelta), ``FuelCorrectedLapTime`` and
    ``FuelCorrectedLapTimeSeconds``.
    """
    out = laps.copy()
    laps_done = pd.to_numeric(out["LapNo"], errors="coerce") - 1
    out["LapTime"] = to_timedelta(out["LapTime"])
    out["FuelCorrection"] = pd.to_timedelta(laps_done * float(correction_per_lap), unit="s")
    out["FuelCorrectedLapTime"] = out["LapTime"] + out["FuelCorrection"]
    out["FuelCorrectedLapTimeSeconds"] = out["FuelCorrectedLapTime"].dt.total_seconds()
    return out


def driver_info(drivers):
    """
    Driver display fields from ``session.drivers`` (a dict of :class:`~livef1.models.driver.Driver`).

    Columns: ``DriverNo``, ``Tla``, ``FullName``, ``FirstName``, ``LastName``,
    ``TeamName``, ``TeamColour`` (``#RRGGBB``, ``None`` if unknown). Ordered by
    driver number.
    """
    columns = ["DriverNo", "Tla", "FullName", "FirstName", "LastName", "TeamName", "TeamColour"]
    rows = []
    for key, driver in (drivers or {}).items():
        number = getattr(driver, "RacingNumber", None) or key
        colour = getattr(driver, "TeamColour", None)
        if colour:
            colour = str(colour).strip()
            colour = colour if colour.startswith("#") else f"#{colour}"
        else:
            colour = None
        full_name = getattr(driver, "FullName", None)
        first, last = getattr(driver, "FirstName", None), getattr(driver, "LastName", None)
        if not full_name and (first or last):
            full_name = " ".join(p for p in (first, last) if p)
        rows.append({
            "DriverNo": str(number),
            "Tla": getattr(driver, "Tla", None),
            "FullName": full_name,
            "FirstName": first,
            "LastName": last,
            "TeamName": getattr(driver, "TeamName", None),
            "TeamColour": colour,
        })
    if not rows:
        return empty_frame(columns)
    df = pd.DataFrame(rows, columns=columns)
    order = pd.to_numeric(df["DriverNo"], errors="coerce")
    return df.assign(_o=order).sort_values(["_o", "DriverNo"], kind="stable").drop(columns="_o").reset_index(drop=True)
