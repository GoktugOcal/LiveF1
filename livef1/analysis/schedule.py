"""Meeting schedule with UTC and track-local session times."""
import re

import pandas as pd

from ._utils import empty_frame

SESSION_SCHEDULE_COLUMNS = [
    "MeetingKey", "MeetingName", "SessionKey", "SessionName", "SessionType",
    "StartLocal", "EndLocal", "StartUtc", "EndUtc", "GmtOffset",
]


def parse_gmt_offset(value):
    """
    Parse a livetiming ``GmtOffset`` into a ``pandas.Timedelta``.

    Accepts ``"03:00:00"``, ``"-05:00:00"``, ``"+03:00"``, ``"+0530"`` and
    ``"03:00"``; returns ``NaT`` for anything else.
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return pd.NaT
    if isinstance(value, pd.Timedelta):
        return value
    text = str(value).strip()
    match = re.fullmatch(r"([+-]?)(\d{1,2}):?(\d{2})(?::?(\d{2}))?", text)
    if not match:
        return pd.NaT
    sign, hours, minutes, seconds = match.groups()
    offset = pd.Timedelta(hours=int(hours), minutes=int(minutes), seconds=int(seconds or 0))
    return -offset if sign == "-" else offset


def _split_local_utc(values, offsets):
    """(local naive, UTC aware) datetimes from livetiming session dates and their offsets."""
    local, utc = [], []
    for value, offset in zip(values, offsets):
        if value is None or pd.isna(value):
            local.append(pd.NaT)
            utc.append(pd.NaT)
            continue
        ts = pd.Timestamp(value)
        if ts.tzinfo is not None:
            # Already absolute: derive the local time from the offset
            u = ts.tz_convert("UTC")
            local.append(u.tz_localize(None) + offset if not pd.isna(offset) else pd.NaT)
            utc.append(u)
        else:
            # Livetiming StartDate/EndDate are track-local wall-clock times
            local.append(ts)
            utc.append((ts - offset).tz_localize("UTC") if not pd.isna(offset) else pd.NaT)
    return pd.to_datetime(pd.Series(local)), pd.to_datetime(pd.Series(utc), utc=True)


def session_schedule(meeting_table):
    """
    Sessions of a meeting with track-local and UTC start/end times.

    Parameters
    ----------
    meeting_table : pandas.DataFrame
        ``Meeting.meeting_table`` (index ``season_year, meeting_location, session_type``),
        or any frame with ``session_key``, ``session_name``, ``session_startDate``,
        ``session_endDate`` and ``gmtoffset``.

    Returns
    -------
    pandas.DataFrame
        ``MeetingKey``, ``MeetingName``, ``SessionKey``, ``SessionName``,
        ``SessionType``, ``StartLocal``, ``EndLocal`` (naive, track-local),
        ``StartUtc``, ``EndUtc`` (UTC-aware) and ``GmtOffset`` (timedelta), ordered by start.
    """
    if meeting_table is None or len(meeting_table) == 0:
        return empty_frame(SESSION_SCHEDULE_COLUMNS)
    df = meeting_table.reset_index() if meeting_table.index.names != [None] else meeting_table.copy()

    def col(name):
        return df[name] if name in df.columns else pd.Series([None] * len(df), index=df.index)

    offsets = col("gmtoffset").map(parse_gmt_offset)
    start_local, start_utc = _split_local_utc(col("session_startDate"), offsets)
    end_local, end_utc = _split_local_utc(col("session_endDate"), offsets)
    out = pd.DataFrame({
        "MeetingKey": col("meeting_key").to_numpy(),
        "MeetingName": col("meeting_name").to_numpy(),
        "SessionKey": col("session_key").to_numpy(),
        "SessionName": col("session_name").to_numpy(),
        "SessionType": col("session_type").to_numpy(),
        "StartLocal": start_local.to_numpy(),
        "EndLocal": end_local.to_numpy(),
        "StartUtc": start_utc,
        "EndUtc": end_utc,
        "GmtOffset": pd.to_timedelta(offsets.to_numpy()),
    })
    return out.sort_values("StartUtc", kind="stable", na_position="last").reset_index(drop=True)
