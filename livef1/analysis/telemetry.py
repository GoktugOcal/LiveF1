"""
Telemetry analyses: lap selection, drive character and the lap-one start.

Functions take frames shaped like LiveF1's silver ``carTelemetry`` table
(``DriverNo``, ``LapNo``, ``timestamp``, ``Speed``, ``Throttle``, ``Brake``,
``Distance``, ``Position`` ...).
"""
import numpy as np
import pandas as pd

from ._utils import add_driver_info, driver_key, empty_frame, to_seconds

DEFAULT_LAP_ONE_DISTANCES = (100, 250, 500, 1000)  # metres from the start line
FULL_THROTTLE_THRESHOLD = 99   # Throttle >= this is full throttle (%)
HEAVY_BRAKING_THRESHOLD = 90   # Brake > this is heavy braking


def _lap_key(value):
    """LapNo as float so ``5``, ``5.0`` and ``np.uint8(5)`` compare equal."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def select_lap_telemetry(telemetry, pairs):
    """
    Telemetry rows whose ``(DriverNo, LapNo)`` is in ``pairs``.

    ``pairs`` is an iterable of ``(driver_no, lap_no)`` tuples or a DataFrame with
    ``DriverNo`` and ``LapNo`` columns. Driver numbers are compared as strings and
    lap numbers as floats, so ``("1", 5)`` matches ``DriverNo=1, LapNo=5.0``. Uses a
    set lookup, far faster than a row-wise ``apply`` on full-session telemetry.
    """
    if hasattr(pairs, "columns"):
        pairs = zip(pairs["DriverNo"], pairs["LapNo"])
    wanted = {(str(d), _lap_key(l)) for d, l in pairs}
    wanted = [key for key in wanted if key[1] is not None and not np.isnan(key[1])]
    if not wanted or len(telemetry) == 0:
        return telemetry.iloc[0:0]
    keys = pd.MultiIndex.from_arrays([
        driver_key(telemetry["DriverNo"]).to_numpy(),
        pd.to_numeric(telemetry["LapNo"], errors="coerce").astype(float).to_numpy(),
    ])
    return telemetry[keys.isin(wanted)]


DRIVE_CHARACTER_COLUMNS = ["DriverNo", "LapNo", "FullThrottlePct", "HeavyBrakingPct", "CorneringPct", "LapDuration"]


def drive_character(telemetry, full_throttle=FULL_THROTTLE_THRESHOLD, heavy_braking=HEAVY_BRAKING_THRESHOLD, driver_info=None):
    """
    Share of time at full throttle, under heavy braking and in between ("cornering").

    Each sample counts for the time until the driver's next sample on the same lap,
    so time deltas never cross drivers or laps. A sample at full throttle counts as
    full throttle even if the brake is pressed.

    Returns
    -------
    pandas.DataFrame
        One row per driver (``LapNo`` is the lap if the driver has one, else ``None``):
        ``FullThrottlePct``, ``HeavyBrakingPct``, ``CorneringPct`` (0-100) and
        ``LapDuration`` (seconds of telemetry counted).
    """
    if len(telemetry) == 0:
        return add_driver_info(empty_frame(DRIVE_CHARACTER_COLUMNS), driver_info)
    tel = pd.DataFrame({
        "DriverNo": driver_key(telemetry["DriverNo"]).to_numpy(),
        "LapNo": telemetry["LapNo"].to_numpy(),
        "t": to_seconds(telemetry["timestamp"]).to_numpy(),
        "Throttle": pd.to_numeric(telemetry["Throttle"], errors="coerce").to_numpy(),
        "Brake": pd.to_numeric(telemetry["Brake"], errors="coerce").to_numpy(),
    }).sort_values(["DriverNo", "LapNo", "t"], kind="stable")
    tel["dt"] = tel.groupby(["DriverNo", "LapNo"])["t"].shift(-1) - tel["t"]
    tel = tel[tel["dt"] > 0]
    full = tel["Throttle"] >= full_throttle
    braking = ~full & (tel["Brake"] > heavy_braking)
    tel["kind"] = np.where(full, "FullThrottlePct", np.where(braking, "HeavyBrakingPct", "CorneringPct"))

    shares = tel.pivot_table(index="DriverNo", columns="kind", values="dt", aggfunc="sum", fill_value=0.0)
    for col in ["FullThrottlePct", "HeavyBrakingPct", "CorneringPct"]:
        if col not in shares.columns:
            shares[col] = 0.0
    total = shares[["FullThrottlePct", "HeavyBrakingPct", "CorneringPct"]].sum(axis=1)
    out = shares[["FullThrottlePct", "HeavyBrakingPct", "CorneringPct"]].div(total, axis=0) * 100
    out["LapDuration"] = total
    laps = tel.groupby("DriverNo")["LapNo"].agg(lambda s: s.iloc[0] if s.nunique() == 1 else None)
    out = out.join(laps).reset_index()
    return add_driver_info(out[DRIVE_CHARACTER_COLUMNS], driver_info)


def _distance_column(d):
    d = float(d)
    return f"{int(d)}m" if d.is_integer() else f"{d:g}m"


def lap_one_start(telemetry, laps=None, grid=None, distances=DEFAULT_LAP_ONE_DISTANCES, speed=100.0, driver_info=None):
    """
    Race start summary per driver from lap-one telemetry.

    Parameters
    ----------
    telemetry : pandas.DataFrame
        Silver ``carTelemetry`` (only ``LapNo == 1`` is used).
    laps : pandas.DataFrame, optional
        Silver ``laps``; the earliest lap-1 ``LapStartTime`` is the start signal.
        Without it the first lap-1 telemetry sample is used.
    grid : dict or pandas.DataFrame, optional
        Grid positions: ``{driver_no: position}`` or a starting grid table with
        ``No.``/``Pos.`` (``session.startingGrid``) or ``DriverNo``/``GridPosition``.
        Without it, the timing position of each driver's first lap-1 sample is used.
    distances : sequence of float
        Distances (metres) at which to report position and speed.
    speed : float
        Target speed (km/h) for the acceleration time.

    Returns
    -------
    pandas.DataFrame
        ``DriverNo``, ``GridPosition``, ``TimeTo{speed}kmh`` (seconds from the start,
        interpolated between samples) and, for each distance ``d``, ``Position_{d}m``,
        ``Speed_{d}m`` and ``PositionsGained_{d}m`` (grid minus position).
        Ordered by grid position.
    """
    time_col = f"TimeTo{_distance_column(speed)[:-1]}kmh"
    columns = ["DriverNo", "GridPosition", time_col]
    for d in distances:
        suffix = _distance_column(d)
        columns += [f"Position_{suffix}", f"Speed_{suffix}", f"PositionsGained_{suffix}"]

    tel = telemetry[pd.to_numeric(telemetry["LapNo"], errors="coerce") == 1].copy()
    if len(tel) == 0:
        return add_driver_info(empty_frame(columns), driver_info)
    tel["DriverNo"] = driver_key(tel["DriverNo"])
    tel["t"] = to_seconds(tel["timestamp"])
    tel = tel.sort_values(["DriverNo", "t"], kind="stable")

    start = None
    if laps is not None and len(laps):
        lap_one = laps[pd.to_numeric(laps["LapNo"], errors="coerce") == 1]
        starts = pd.to_timedelta(lap_one["LapStartTime"], errors="coerce").dropna()
        if len(starts):
            start = starts.min().total_seconds()
    if start is None:
        start = tel["t"].min()

    grid_map = {}
    if isinstance(grid, dict):
        grid_map = {str(k): v for k, v in grid.items()}
    elif grid is not None and len(grid):
        if {"No.", "Pos."} <= set(grid.columns):
            grid_map = {str(k): v for k, v in zip(grid["No."], grid["Pos."])}
        elif {"DriverNo", "GridPosition"} <= set(grid.columns):
            grid_map = {str(k): v for k, v in zip(grid["DriverNo"], grid["GridPosition"])}

    rows = []
    for driver_no, lap in tel.groupby("DriverNo", sort=False):
        row = {"DriverNo": driver_no}
        grid_pos = pd.to_numeric(pd.Series([grid_map.get(driver_no)]), errors="coerce").iloc[0]
        if pd.isna(grid_pos) and "Position" in lap.columns:
            first = pd.to_numeric(lap["Position"], errors="coerce").dropna()
            grid_pos = first.iloc[0] if len(first) else np.nan
        row["GridPosition"] = grid_pos

        moving = lap[lap["t"] >= start]
        v = pd.to_numeric(moving["Speed"], errors="coerce").to_numpy()
        t = moving["t"].to_numpy()
        above = np.flatnonzero(v >= speed)
        if len(above) == 0:
            row[time_col] = np.nan
        elif above[0] == 0:
            row[time_col] = t[0] - start
        else:
            i = above[0]
            frac = (speed - v[i - 1]) / (v[i] - v[i - 1]) if v[i] != v[i - 1] else 1.0
            row[time_col] = t[i - 1] + frac * (t[i] - t[i - 1]) - start

        dist = pd.to_numeric(lap["Distance"], errors="coerce") if "Distance" in lap.columns else pd.Series(np.nan, index=lap.index)
        for d in distances:
            suffix = _distance_column(d)
            reached = lap[dist >= d]
            if len(reached):
                sample = reached.iloc[0]
                pos = pd.to_numeric(pd.Series([sample.get("Position")]), errors="coerce").iloc[0]
                row[f"Position_{suffix}"] = pos
                row[f"Speed_{suffix}"] = float(sample["Speed"]) if pd.notna(sample["Speed"]) else np.nan
                row[f"PositionsGained_{suffix}"] = grid_pos - pos if pd.notna(grid_pos) and pd.notna(pos) else np.nan
            else:
                row[f"Position_{suffix}"] = row[f"Speed_{suffix}"] = row[f"PositionsGained_{suffix}"] = np.nan
        rows.append(row)

    out = pd.DataFrame(rows, columns=columns)
    out = out.sort_values(["GridPosition", "DriverNo"], kind="stable", na_position="last").reset_index(drop=True)
    return add_driver_info(out, driver_info)
