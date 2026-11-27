"""Next and previous sessions and meetings, without loading a season.

The calendar comes from Jolpica, which lists every session of the season in UTC
before the weekend starts and needs no F1 account. Once live timing lists a
meeting in its season index (an F1 account is needed, see :func:`livef1.login`),
its session keys, data paths and exact end times are used instead.

"Next" means not ended yet, so a running session or meeting is the next one;
"previous" means ended. Together they cover every moment.
"""

from __future__ import annotations

import time
import unicodedata
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

import pandas as pd

from .adapters.jolpicaf1_adapter import jolpica_client
from .adapters.livetimingf1_adapter import livetimingF1_request
from .analysis.schedule import parse_gmt_offset
from .utils.exceptions import AuthenticationError, InvalidEndpointError, LiveF1Error
from .utils.logger import logger

__all__ = [
    "ScheduledSession",
    "ScheduledMeeting",
    "SessionStatus",
    "next_session",
    "previous_session",
    "next_meeting",
    "previous_meeting",
]

UTC = timezone.utc

# Session lengths used until live timing lists the session's real end time
_DEFAULT_MINUTES = {
    "practice": 60,
    "qualifying": 60,
    "sprint qualifying": 45,
    "sprint shootout": 45,
    "sprint": 60,
    "race": 120,
}

# Jolpica race fields -> (session name, type, number)
_JOLPICA_SESSIONS = (
    ("FirstPractice", "Practice 1", "Practice", 1),
    ("SecondPractice", "Practice 2", "Practice", 2),
    ("ThirdPractice", "Practice 3", "Practice", 3),
    ("SprintShootout", "Sprint Shootout", "Qualifying", None),
    ("SprintQualifying", "Sprint Qualifying", "Qualifying", None),
    ("Qualifying", "Qualifying", "Qualifying", None),
    ("Sprint", "Sprint", "Race", None),
)

LIVE_STATES = {"Started", "Aborted"}
FINISHED_STATES = {"Finished", "Finalised", "Ends"}

# Seconds a cached response is reused
_TTL_JOLPICA = 3600
_TTL_LIVETIMING_INDEX = 120
_TTL_LATEST = 20
_TTL_FAILED = 60

_cache: dict = {}
_warned: set = set()


# --------------------------------------------------------------------------- helpers

def _now(now=None) -> datetime:
    """``now`` as an aware UTC datetime. Naive values are read as UTC."""
    if now is None:
        return datetime.now(UTC)
    if not isinstance(now, datetime):
        now = pd.Timestamp(now).to_pydatetime()
    return now.replace(tzinfo=UTC) if now.tzinfo is None else now.astimezone(UTC)


def _norm(value) -> str:
    """Casefolded, accent-free text, so "São Paulo" matches "Sao Paulo"."""
    if value is None:
        return ""
    text = unicodedata.normalize("NFKD", str(value))
    return "".join(c for c in text if not unicodedata.combining(c)).strip().casefold()


def _cached(key, ttl, fetch, refresh=False):
    hit = _cache.get(key)
    if hit and not refresh and hit[0] > time.monotonic():
        return hit[1]
    value, ok = fetch()
    _cache[key] = (time.monotonic() + (ttl if ok else _TTL_FAILED), value)
    return value


@contextmanager
def _quiet():
    """Silence LiveF1's own logging for an expected failure (an index not published yet)."""
    was = logger.disabled
    logger.disabled = True
    try:
        yield
    finally:
        logger.disabled = was


def _livetiming_json(endpoint):
    with _quiet():
        return livetimingF1_request(endpoint)


def _parse_utc(text) -> datetime | None:
    try:
        ts = pd.Timestamp(text)
    except (ValueError, TypeError):
        return None
    ts = ts.tz_localize(UTC) if ts.tzinfo is None else ts.tz_convert(UTC)
    return ts.to_pydatetime()


def _livetiming_times(session: dict):
    """(start UTC, end UTC, gmt offset) of a live timing session entry."""
    offset = parse_gmt_offset(session.get("GmtOffset"))
    offset = None if pd.isna(offset) else offset.to_pytimedelta()

    def utc(text):
        if not text:
            return None
        ts = pd.Timestamp(text)
        if ts.tzinfo is not None:
            return ts.tz_convert(UTC).to_pydatetime()
        if offset is None:
            return None
        # live timing dates are track-local wall-clock times
        return (ts.to_pydatetime() - offset).replace(tzinfo=UTC)

    return utc(session.get("StartDate")), utc(session.get("EndDate")), offset


def _default_end(name, type_, start):
    minutes = _DEFAULT_MINUTES.get(_norm(name)) or _DEFAULT_MINUTES.get(_norm(type_), 60)
    return start + timedelta(minutes=minutes)


def _name_matches(session, names) -> bool:
    if names is None:
        return True
    if isinstance(names, str):
        names = [names]
    for name in names:
        n = _norm(name)
        if n == _norm(session.name) or (n == "practice" and _norm(session.type) == "practice"):
            return True
        if n in ("sprint qualifying", "sprint shootout") and _norm(session.name) in ("sprint qualifying", "sprint shootout"):
            return True
    return False


# --------------------------------------------------------------------------- data classes

@dataclass(frozen=True)
class SessionStatus:
    """
    State of a session in live timing, from its ``SessionInfo.json``.

    Attributes
    ----------
    session_status : str or None
        ``"Inactive"`` (not started), ``"Started"``, ``"Aborted"`` (stopped, for
        example under a red flag), ``"Finished"``, ``"Finalised"`` or ``"Ends"``.
    archive_status : str or None
        ``"Generating"`` while the session's data is still being written,
        ``"Complete"`` once it is.
    """
    key: int | None
    name: str | None
    meeting: str | None
    path: str | None
    session_status: str | None
    archive_status: str | None
    start: datetime | None
    end: datetime | None
    raw: dict = field(default_factory=dict, repr=False, compare=False)

    @property
    def is_live(self) -> bool:
        """The session is running (``Started``) or stopped mid-session (``Aborted``)."""
        return self.session_status in LIVE_STATES

    @property
    def is_finished(self) -> bool:
        return self.session_status in FINISHED_STATES

    @property
    def is_data_available(self) -> bool:
        """The session is over and live timing has finished writing its data."""
        return self.archive_status == "Complete" and not self.is_live and self.session_status != "Inactive"

    @classmethod
    def from_session_info(cls, info: dict) -> "SessionStatus":
        start, end, _ = _livetiming_times(info)
        archive = info.get("ArchiveStatus")
        if isinstance(archive, dict):
            archive = archive.get("Status")
        return cls(
            key=info.get("Key"),
            name=info.get("Name"),
            meeting=(info.get("Meeting") or {}).get("Name"),
            path=info.get("Path"),
            session_status=info.get("SessionStatus"),
            archive_status=archive,
            start=start,
            end=end,
            raw=info,
        )


@dataclass(frozen=True)
class ScheduledSession:
    """
    A session of the calendar.

    ``start`` and ``end`` are aware UTC datetimes. ``key``, ``meeting_key`` and
    ``path`` are ``None`` until live timing lists the session (``listed``); until
    then ``end`` is estimated from the session type (``end_estimated``).
    """
    season: int
    meeting: str
    name: str
    type: str | None
    start: datetime
    end: datetime
    round: int | None = None
    number: int | None = None
    key: int | None = None
    meeting_key: int | None = None
    path: str | None = None
    gmt_offset: timedelta | None = None
    end_estimated: bool = False

    @property
    def listed(self) -> bool:
        """Live timing lists the session in its season index."""
        return self.path is not None

    @property
    def start_local(self) -> datetime | None:
        """Start in track-local time, once live timing gives the track's GMT offset."""
        return None if self.gmt_offset is None else self.start.astimezone(timezone(self.gmt_offset))

    def is_live(self, now=None) -> bool:
        """Running at ``now`` by the calendar. For live timing's view use :meth:`status`."""
        return self.start <= _now(now) < self.end

    def status(self, refresh: bool = False) -> SessionStatus | None:
        """
        Live timing's state of the session, or ``None`` if live timing has none yet.

        For the session live timing currently shows, this reads the public
        ``static/SessionInfo.json`` and needs no F1 account. Any other session
        is read from its own ``SessionInfo.json``, which needs one.

        Raises
        ------
        AuthenticationError
            If the session is not the current one and no F1 account is available.
        """
        latest = _latest_status(refresh)
        if latest is not None and _same_session(self, latest):
            return latest
        if not self.path:
            return None
        try:
            return SessionStatus.from_session_info(_livetiming_json(self.path + "SessionInfo.json"))
        except InvalidEndpointError:
            return None

    def load(self):
        """The full :class:`livef1.Session`, to download its data. Needs ``listed``."""
        from .api import get_session
        if self.key is None:
            raise LiveF1Error(f"{self.meeting} {self.name} is not listed in live timing yet.")
        return get_session(self.season, meeting_key=self.meeting_key, session_key=self.key)


@dataclass(frozen=True)
class ScheduledMeeting:
    """A meeting of the calendar and its sessions, in start order. Testing has no ``race``."""
    season: int
    name: str
    sessions: tuple
    round: int | None = None
    official_name: str | None = None
    location: str | None = None
    country: str | None = None
    circuit: str | None = None
    key: int | None = None

    @property
    def race(self) -> ScheduledSession | None:
        return self.session("Race")

    @property
    def start(self) -> datetime:
        return self.sessions[0].start

    @property
    def end(self) -> datetime:
        return max(s.end for s in self.sessions)

    def session(self, name) -> ScheduledSession | None:
        """The first session called ``name`` ("Race", "Qualifying", "Sprint", "Practice 1", ...)."""
        return next((s for s in self.sessions if _name_matches(s, name)), None)

    def load(self):
        """The full :class:`livef1.Meeting`."""
        from .api import get_meeting
        if self.key is not None:
            return get_meeting(self.season, meeting_key=self.key)
        return get_meeting(self.season, meeting_identifier=self.name)


# --------------------------------------------------------------------------- calendar

def _fetch_jolpica_races(season, refresh=False):
    def fetch():
        try:
            races = jolpica_client.query().season(season).get_races().data.races or []
            return [r.to_dict() for r in races], True
        except Exception as exc:
            logger.debug(f"Jolpica calendar for {season} failed: {exc}")
            return [], False
    return _cached(("jolpica", season), _TTL_JOLPICA, fetch, refresh)


def _fetch_livetiming_index(season, refresh=False):
    def fetch():
        try:
            return _livetiming_json(f"{season}/Index.json").get("Meetings") or [], True
        except AuthenticationError as exc:
            if "auth" not in _warned:
                _warned.add("auth")
                logger.warning(
                    f"Live timing season index needs an F1 account ({exc}). "
                    "Using the Jolpica calendar only: no session keys or paths until you sign in."
                )
            return [], False
        except InvalidEndpointError:
            return [], True  # season not in live timing yet
        except Exception as exc:
            logger.debug(f"Live timing season index for {season} failed: {exc}")
            return [], False
    return _cached(("livetiming", season), _TTL_LIVETIMING_INDEX, fetch, refresh)


def _jolpica_sessions(season, race: dict):
    rnd = int(race["round"]) if race.get("round") else None
    entries = [(race.get(k), name, type_, number) for k, name, type_, number in _JOLPICA_SESSIONS]
    entries.append(({"date": race.get("date"), "time": race.get("time")}, "Race", "Race", None))
    out = []
    for entry, name, type_, number in entries:
        if not entry or not entry.get("date"):
            continue
        start = _parse_utc(f"{entry['date']}T{(entry.get('time') or '00:00:00').rstrip('Z')}")
        if start is None:
            continue
        out.append(ScheduledSession(
            season=season, meeting=race.get("raceName"), name=name, type=type_, number=number,
            start=start, end=_default_end(name, type_, start), round=rnd, end_estimated=True,
        ))
    return out


def _livetiming_sessions(season, meeting: dict, rnd=None, meeting_name=None):
    out = []
    for s in meeting.get("Sessions") or []:
        name = s.get("Name") or s.get("Type")
        start, end, offset = _livetiming_times(s)
        if not name or start is None:
            continue
        out.append(ScheduledSession(
            season=season, meeting=meeting_name or meeting.get("Name"), name=name, type=s.get("Type"),
            number=s.get("Number"), start=start, end=end or _default_end(name, s.get("Type"), start),
            round=rnd, key=s.get("Key"), meeting_key=meeting.get("Key"), path=s.get("Path"),
            gmt_offset=offset, end_estimated=end is None,
        ))
    return out


def _match_meeting(name, sessions, meetings, used):
    target = _norm(name)
    for i, m in enumerate(meetings):
        if i not in used and _norm(m.get("Name")) == target:
            return i
    # names differ between the sources now and then: fall back on a session starting at the same time
    starts = [s.start for s in sessions]
    for i, m in enumerate(meetings):
        if i in used:
            continue
        for s in m.get("Sessions") or []:
            start, _, _ = _livetiming_times(s)
            if start and any(abs(start - t) <= timedelta(minutes=90) for t in starts):
                return i
    return None


def _merge_sessions(jolpica, livetiming):
    """Live timing entries win; Jolpica sessions live timing does not list yet are kept."""
    merged = list(livetiming)
    for j in jolpica:
        if not any(
            _norm(l.name) == _norm(j.name) or abs(l.start - j.start) <= timedelta(minutes=90)
            for l in livetiming
        ):
            merged.append(j)
    return tuple(sorted(merged, key=lambda s: s.start))


def _season_meetings(season: int, refresh=False) -> list:
    """Every meeting of ``season`` in date order, Jolpica and live timing merged."""
    races = _fetch_jolpica_races(season, refresh)
    meetings = _fetch_livetiming_index(season, refresh)
    used, out = set(), []
    for race in races:
        j = _jolpica_sessions(season, race)
        i = _match_meeting(race.get("raceName"), j, meetings, used)
        m = meetings[i] if i is not None else {}
        if i is not None:
            used.add(i)
        rnd = int(race["round"]) if race.get("round") else None
        sessions = _merge_sessions(j, _livetiming_sessions(season, m, rnd, race.get("raceName")))
        if not sessions:
            continue
        loc = (race.get("Circuit") or {}).get("Location") or {}
        out.append(ScheduledMeeting(
            season=season, name=race.get("raceName"), sessions=sessions, round=rnd,
            official_name=m.get("OfficialName"),
            location=m.get("Location") or loc.get("locality"),
            country=(m.get("Country") or {}).get("Name") or loc.get("country"),
            circuit=(race.get("Circuit") or {}).get("circuitName") or (m.get("Circuit") or {}).get("ShortName"),
            key=m.get("Key"),
        ))
    # testing and other meetings only live timing lists
    for i, m in enumerate(meetings):
        if i in used:
            continue
        sessions = tuple(sorted(_livetiming_sessions(season, m), key=lambda s: s.start))
        if sessions:
            out.append(ScheduledMeeting(
                season=season, name=m.get("Name"), sessions=sessions, official_name=m.get("OfficialName"),
                location=m.get("Location"), country=(m.get("Country") or {}).get("Name"),
                circuit=(m.get("Circuit") or {}).get("ShortName"), key=m.get("Key"),
            ))
    return sorted(out, key=lambda m: m.start)


def _meetings_near(now: datetime, refresh=False) -> list:
    """Meetings of the year of ``now``, plus the neighbouring year near its ends."""
    out = _season_meetings(now.year, refresh)
    if not out or now >= out[-1].end - timedelta(days=21):
        out += _season_meetings(now.year + 1, refresh)
    if not out or now <= out[0].start + timedelta(days=21):
        out = _season_meetings(now.year - 1, refresh) + out
    return out


def _sessions(now, refresh, name):
    return [s for m in _meetings_near(now, refresh) for s in m.sessions if _name_matches(s, name)]


def next_session(name=None, now=None, refresh: bool = False) -> ScheduledSession | None:
    """
    The next session that has not ended: the one running, else the next to start.

    Parameters
    ----------
    name : str or list of str, optional
        Only sessions with this name: ``"Race"``, ``"Qualifying"``, ``"Sprint"``,
        ``"Sprint Qualifying"``, ``"Practice 1"``, or ``"Practice"`` for any practice.
    now : datetime, pandas.Timestamp or str, optional
        The moment to look from. Default: now. Naive values are UTC.
    refresh : bool
        Fetch the calendar again instead of using the cache (Jolpica is cached
        for an hour, the live timing index for two minutes).

    Examples
    --------
    >>> s = livef1.next_session()
    >>> s.meeting, s.name, s.start, s.is_live()
    >>> livef1.next_session("Race").start
    """
    now = _now(now)
    return min((s for s in _sessions(now, refresh, name) if s.end > now), key=lambda s: s.start, default=None)


def previous_session(name=None, now=None, refresh: bool = False) -> ScheduledSession | None:
    """
    The last session that has ended. Parameters as in :func:`next_session`.

    Examples
    --------
    >>> s = livef1.previous_session()
    >>> s.status().is_data_available
    >>> s.load().generate()
    """
    now = _now(now)
    return max((s for s in _sessions(now, refresh, name) if s.end <= now), key=lambda s: s.end, default=None)


def next_meeting(now=None, refresh: bool = False) -> ScheduledMeeting | None:
    """
    The next meeting that has not ended: the one under way, else the next to start.

    A meeting lasts until its last session ends. Pre-season testing counts as a meeting
    (its ``race`` is ``None``). ``now`` and ``refresh`` as in :func:`next_session`.

    Examples
    --------
    >>> m = livef1.next_meeting()
    >>> m.name, m.round, m.race.start
    >>> [s.name for s in m.sessions]
    """
    now = _now(now)
    return next((m for m in _meetings_near(now, refresh) if m.end > now), None)


def previous_meeting(now=None, refresh: bool = False) -> ScheduledMeeting | None:
    """The last meeting that has ended. ``now`` and ``refresh`` as in :func:`next_session`."""
    now = _now(now)
    return max((m for m in _meetings_near(now, refresh) if m.end <= now), key=lambda m: m.end, default=None)


# --------------------------------------------------------------------------- live timing status

def _latest_status(refresh=False) -> SessionStatus | None:
    """The session live timing shows now, from the public ``static/SessionInfo.json``."""
    def fetch():
        try:
            return SessionStatus.from_session_info(_livetiming_json("SessionInfo.json")), True
        except Exception as exc:
            logger.debug(f"Live timing SessionInfo.json failed: {exc}")
            return None, False
    return _cached(("latest",), _TTL_LATEST, fetch, refresh)


def _same_session(session: ScheduledSession, status: SessionStatus) -> bool:
    if session.key is not None and status.key is not None:
        return session.key == status.key
    if session.path and status.path:
        return session.path == status.path
    if _norm(session.name) != _norm(status.name):
        return False
    if status.start is not None:
        return abs(status.start - session.start) <= timedelta(hours=3)
    return _norm(session.meeting) == _norm(status.meeting)
