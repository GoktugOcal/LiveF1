"""
Track analyses: neutralisation windows (SC / VSC / red flag), circuit map rotation,
track regions, time per region, track dominance and distance-based gaps.
"""
import numpy as np
import pandas as pd

from ._utils import driver_key, empty_frame, to_seconds

#: Track status code -> event label. VSC ending ("7") still belongs to the VSC window.
TRACK_EVENT_CODES = {"4": "SC", "5": "RED", "6": "VSC", "7": "VSC"}

TRACK_EVENTS_COLUMNS = ["Event", "StartTime", "EndTime", "StartLap", "EndLap", "StartDate", "EndDate", "Duration"]


def _race_lap_at(laps, times):
    """Leader's lap (highest lap any driver has started) at each session time."""
    if laps is None or len(laps) == 0:
        return [None] * len(times)
    starts = laps[["LapNo", "LapStartTime"]].copy()
    starts["LapStartTime"] = pd.to_timedelta(starts["LapStartTime"], errors="coerce")
    starts["LapNo"] = pd.to_numeric(starts["LapNo"], errors="coerce")
    first_start = starts.dropna().groupby("LapNo")["LapStartTime"].min().sort_index()
    # Lap N starts when the first car starts it; keep the start times increasing
    first_start = first_start.cummax()
    if first_start.empty:
        return [None] * len(times)
    lap_nos = first_start.index.to_numpy()
    start_values = first_start.to_numpy()
    out = []
    for t in times:
        if pd.isna(t):
            out.append(int(lap_nos[-1]))
            continue
        pos = np.searchsorted(start_values, pd.Timedelta(t).to_timedelta64(), side="right") - 1
        out.append(int(lap_nos[max(pos, 0)]))
    return out


def track_events(track_status, laps=None, first_datetime=None):
    """
    Safety car, virtual safety car and red flag windows from the ``TrackStatus`` topic.

    A window starts at the first status of its kind (``4`` SC, ``6``/``7`` VSC, ``5``
    red flag) and ends at the next status of another kind. A window still open at
    the end of the data has ``EndTime`` ``NaT``.

    Parameters
    ----------
    track_status : pandas.DataFrame
        Bronze ``TrackStatus``: ``timestamp`` (session time) and ``Status``.
    laps : pandas.DataFrame, optional
        Silver ``laps``; used to give each window the leader's lap at its start and end
        (``StartLap``/``EndLap``: laps that were at least partly neutralised).
    first_datetime : datetime-like, optional
        UTC datetime of session time zero (``session.first_datetime``), used for
        ``StartDate``/``EndDate``.

    Returns
    -------
    pandas.DataFrame
        ``Event``, ``StartTime``, ``EndTime``, ``StartLap``, ``EndLap``,
        ``StartDate``, ``EndDate``, ``Duration``.
    """
    if track_status is None or len(track_status) == 0:
        return empty_frame(TRACK_EVENTS_COLUMNS)
    ts = track_status[["timestamp", "Status"]].copy()
    ts["timestamp"] = pd.to_timedelta(ts["timestamp"], errors="coerce")
    ts["Status"] = ts["Status"].astype(str)
    ts = ts.dropna(subset=["timestamp"]).sort_values("timestamp", kind="stable")

    windows = []
    current = None
    for t, status in zip(ts["timestamp"], ts["Status"]):
        label = TRACK_EVENT_CODES.get(status)
        if current is not None and label != current["Event"]:
            current["EndTime"] = t
            windows.append(current)
            current = None
        if label is not None and current is None:
            current = {"Event": label, "StartTime": t, "EndTime": pd.NaT}
    if current is not None:
        windows.append(current)

    if not windows:
        return empty_frame(TRACK_EVENTS_COLUMNS)
    events = pd.DataFrame(windows)
    events["StartTime"] = pd.to_timedelta(events["StartTime"])
    events["EndTime"] = pd.to_timedelta(events["EndTime"])
    events["StartLap"] = _race_lap_at(laps, events["StartTime"])
    events["EndLap"] = _race_lap_at(laps, events["EndTime"])
    if first_datetime is not None:
        origin = pd.Timestamp(first_datetime)
        events["StartDate"] = origin + events["StartTime"]
        events["EndDate"] = origin + events["EndTime"]
    else:
        events["StartDate"] = pd.NaT
        events["EndDate"] = pd.NaT
    events["Duration"] = events["EndTime"] - events["StartTime"]
    return events[TRACK_EVENTS_COLUMNS]


def track_events_by_type(events):
    """``{"sc": [(start_lap, end_lap), ...], "virtual_sc": [...], "red": [...]}`` from :func:`track_events`."""
    keys = {"SC": "sc", "VSC": "virtual_sc", "RED": "red"}
    out = {"red": [], "virtual_sc": [], "sc": []}
    for _, row in events.iterrows():
        out[keys[row["Event"]]].append((row["StartLap"], row["EndLap"]))
    return out


def corners_table(raw_corners):
    """
    Corners from the circuit API's ``corners`` list: ``Number``, ``Letter``, ``Name``,
    ``Distance`` (metres from the line), ``X``, ``Y``, ``Angle``.
    """
    columns = ["Number", "Letter", "Name", "Distance", "X", "Y", "Angle"]
    rows = []
    for corner in raw_corners or []:
        position = corner.get("trackPosition") or {}
        number = corner.get("number")
        letter = corner.get("letter") or ""
        rows.append({
            "Number": number,
            "Letter": letter,
            "Name": f"T{number}{letter}" if number is not None else None,
            "Distance": corner["length"] / 10 if corner.get("length") is not None else np.nan,
            "X": position.get("x", corner.get("x")),
            "Y": position.get("y", corner.get("y")),
            "Angle": corner.get("angle"),
        })
    if not rows:
        return empty_frame(columns)
    df = pd.DataFrame(rows, columns=columns)
    return df.sort_values("Distance", kind="stable").reset_index(drop=True)


def rotate_xy(df, degrees, x="X", y="Y", angle=None):
    """
    Rotate ``X``/``Y`` coordinates counter-clockwise by ``degrees`` around the origin.

    Returns a copy. If ``angle`` names a column (e.g. ``"Angle"`` of the corners
    table), ``degrees`` is added to it so corner labels keep pointing outwards.
    """
    out = df.copy()
    if not degrees:
        return out
    theta = np.deg2rad(degrees)
    xs = out[x].astype(float).to_numpy()
    ys = out[y].astype(float).to_numpy()
    out[x] = xs * np.cos(theta) - ys * np.sin(theta)
    out[y] = xs * np.sin(theta) + ys * np.cos(theta)
    if angle is not None and angle in out.columns:
        out[angle] = out[angle] + degrees
    return out


def rotate_circuit(telemetry, corners, degrees):
    """Rotate a telemetry frame and the corners table together; returns ``(telemetry, corners)``."""
    return rotate_xy(telemetry, degrees), rotate_xy(corners, degrees, angle="Angle")


def assign_track_regions(telemetry, regions, distance="Distance"):
    """
    Name of the track region of each telemetry sample.

    ``regions`` has ``name``, ``corner_start`` and ``corner_end`` (metres); a region with
    ``corner_end < corner_start`` wraps around the start line.
    """
    d = telemetry[distance]
    conditions = [
        ((d >= row["corner_start"]) & (d < row["corner_end"]))
        if row["corner_end"] >= row["corner_start"]
        else ((d >= row["corner_start"]) | (d < row["corner_end"]))
        for _, row in regions.iterrows()
    ]
    if not conditions:
        return np.full(len(telemetry), None, dtype=object)
    return np.select(conditions, regions["name"].tolist(), default=None)


def _lap_clock(lap):
    """(distance, seconds) arrays of one lap, sorted by distance, increasing distance only."""
    lap = lap.dropna(subset=["Distance", "timestamp"]).sort_values("timestamp", kind="stable")
    dist = lap["Distance"].astype(float).to_numpy()
    secs = to_seconds(lap["timestamp"]).to_numpy()
    if len(dist) == 0:
        return dist, secs
    keep = np.concatenate([[True], np.diff(np.maximum.accumulate(dist)) > 0])
    return dist[keep], secs[keep]


def track_region_times(telemetry, regions):
    """
    Seconds each driver spent in each track region, per lap.

    The time at each region boundary is interpolated from distance, so regions shorter
    than the sampling interval still get a time. Regions that wrap past the line are
    split into the part before and after the line.

    Returns
    -------
    pandas.DataFrame
        ``DriverNo``, ``LapNo``, ``TrackRegion``, ``Time`` (seconds).
    """
    rows = []
    tel = telemetry.copy()
    tel["DriverNo"] = driver_key(tel["DriverNo"])
    for (driver_no, lap_no), lap in tel.groupby(["DriverNo", "LapNo"], sort=True):
        dist, secs = _lap_clock(lap)
        if len(dist) < 2:
            continue
        lo, hi = dist[0], dist[-1]

        def clock(d):
            return float(np.interp(np.clip(d, lo, hi), dist, secs))

        for _, region in regions.iterrows():
            start, end = float(region["corner_start"]), float(region["corner_end"])
            if end >= start:
                spent = clock(end) - clock(start)
            else:
                spent = (clock(hi) - clock(start)) + (clock(end) - clock(lo))
            rows.append({"DriverNo": driver_no, "LapNo": lap_no, "TrackRegion": region["name"], "Time": spent})
    if not rows:
        return empty_frame(["DriverNo", "LapNo", "TrackRegion", "Time"])
    return pd.DataFrame(rows)


def track_dominance(region_times):
    """
    Fastest driver in each region from :func:`track_region_times` output.

    When a driver has several laps, their fastest time in the region counts.

    Returns
    -------
    pandas.DataFrame
        ``TrackRegion``, ``DriverNo`` (fastest), ``Time``, ``GapToSecond`` (seconds,
        ``NaN`` with one driver).
    """
    columns = ["TrackRegion", "DriverNo", "Time", "GapToSecond"]
    if len(region_times) == 0:
        return empty_frame(columns)
    best = region_times.groupby(["TrackRegion", "DriverNo"], sort=False)["Time"].min().reset_index()
    rows = []
    for region, group in best.groupby("TrackRegion", sort=False):
        group = group.sort_values("Time", kind="stable")
        gap = group["Time"].iloc[1] - group["Time"].iloc[0] if len(group) > 1 else np.nan
        rows.append({"TrackRegion": region, "DriverNo": group["DriverNo"].iloc[0], "Time": group["Time"].iloc[0], "GapToSecond": gap})
    order = {name: i for i, name in enumerate(region_times["TrackRegion"].drop_duplicates())}
    out = pd.DataFrame(rows, columns=columns)
    return out.assign(_o=out["TrackRegion"].map(order)).sort_values("_o").drop(columns="_o").reset_index(drop=True)


def gap_between_drivers(telemetry, reference_driver, drivers=None, step=10.0):
    """
    Time gap along the lap between a reference driver and other drivers.

    ``telemetry`` should hold one lap per driver (e.g. from
    :meth:`~livef1.models.session.Session.get_lap_telemetry`). Each lap's elapsed time
    is interpolated onto a common distance grid every ``step`` metres.

    Returns
    -------
    pandas.DataFrame
        ``Distance``, ``DriverNo``, ``Time`` (seconds since the lap's first sample),
        ``Gap`` (seconds; positive = behind the reference driver at that distance).
    """
    tel = telemetry.copy()
    tel["DriverNo"] = driver_key(tel["DriverNo"])
    reference_driver = str(reference_driver)
    drivers = [str(d) for d in (drivers if drivers is not None else tel["DriverNo"].dropna().unique())]
    if reference_driver not in drivers:
        drivers = [reference_driver] + drivers

    clocks = {}
    for driver_no in drivers:
        lap = tel[tel["DriverNo"] == driver_no]
        dist, secs = _lap_clock(lap)
        if len(dist) >= 2:
            clocks[driver_no] = (dist, secs - secs[0])
    if reference_driver not in clocks:
        return empty_frame(["Distance", "DriverNo", "Time", "Gap"])

    lo = max(c[0][0] for c in clocks.values())
    hi = min(c[0][-1] for c in clocks.values())
    grid = np.arange(np.ceil(lo / step) * step, hi + 1e-9, step) if hi > lo else np.array([lo])
    ref_time = np.interp(grid, *clocks[reference_driver])
    frames = []
    for driver_no in drivers:
        if driver_no not in clocks:
            continue
        time = np.interp(grid, *clocks[driver_no])
        frames.append(pd.DataFrame({"Distance": grid, "DriverNo": driver_no, "Time": time, "Gap": time - ref_time}))
    return pd.concat(frames, ignore_index=True)
