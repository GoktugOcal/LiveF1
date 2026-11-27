"""Tests for livef1.schedule: next/previous sessions and meetings, session status (offline)."""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

import pandas as pd
import pytest

import livef1
from livef1 import schedule as sch
from livef1.utils.exceptions import AuthenticationError, InvalidEndpointError, LiveF1Error

UTC = timezone.utc


def _race(rnd, name, race_dt, sessions, country="Qatar"):
    d = {
        "season": "2026", "round": str(rnd), "raceName": name,
        "Circuit": {"circuitName": f"{name} circuit", "Location": {"locality": "Town", "country": country}},
        "date": race_dt[:10], "time": race_dt[11:] + "Z",
    }
    for key, dt in sessions.items():
        d[key] = {"date": dt[:10], "time": dt[11:] + "Z"}
    return SimpleNamespace(to_dict=lambda d=d: d)


JOLPICA = [
    _race(21, "Las Vegas Grand Prix", "2026-11-22T04:00:00", {
        "FirstPractice": "2026-11-20T00:30:00", "Qualifying": "2026-11-21T04:00:00",
    }, country="USA"),
    _race(22, "Qatar Grand Prix", "2026-11-29T16:00:00", {
        "FirstPractice": "2026-11-27T13:30:00",
        "SprintQualifying": "2026-11-27T17:30:00",
        "Sprint": "2026-11-28T14:00:00",
        "Qualifying": "2026-11-28T18:00:00",
    }),
]

VEGAS = "2026/2026-11-21_Las_Vegas_Grand_Prix/"
LIVETIMING_INDEX = {
    "Year": 2026,
    "Meetings": [
        {
            "Key": 1290, "Name": "Pre-Season Testing", "Location": "Sakhir",
            "Country": {"Name": "Bahrain"}, "Circuit": {"ShortName": "Sakhir"},
            "Sessions": [
                {"Key": 1, "Type": "Practice", "Number": 1, "Name": "Day 1",
                 "StartDate": "2026-02-11T10:00:00", "EndDate": "2026-02-11T19:00:00",
                 "GmtOffset": "03:00:00", "Path": "2026/T/Day_1/"},
            ],
        },
        {
            # live timing spells it differently than Jolpica
            "Key": 1300, "Name": "Las Végas Grand Prix", "OfficialName": "FORMULA 1 LAS VEGAS GRAND PRIX 2026",
            "Location": "Las Vegas", "Country": {"Name": "United States"}, "Circuit": {"ShortName": "Las Vegas"},
            "Sessions": [
                {"Key": 11413, "Type": "Practice", "Number": 1, "Name": "Practice 1",
                 "StartDate": "2026-11-19T16:30:00", "EndDate": "2026-11-19T17:30:00",
                 "GmtOffset": "-08:00:00", "Path": VEGAS + "2026-11-19_Practice_1/"},
                {"Key": 11416, "Type": "Qualifying", "Name": "Qualifying",
                 "StartDate": "2026-11-20T20:00:00", "EndDate": "2026-11-20T21:00:00",
                 "GmtOffset": "-08:00:00", "Path": VEGAS + "2026-11-20_Qualifying/"},
                {"Key": 11420, "Type": "Race", "Name": "Race",
                 "StartDate": "2026-11-21T20:00:00", "EndDate": "2026-11-21T22:05:00",
                 "GmtOffset": "-08:00:00", "Path": VEGAS + "2026-11-21_Race/"},
            ],
        },
    ],
}


def _info(key, name, path, status, archive, start, end, meeting="Las Vegas Grand Prix", offset="-08:00:00"):
    return {
        "Meeting": {"Key": 1300, "Name": meeting}, "SessionStatus": status,
        "ArchiveStatus": {"Status": archive}, "Key": key, "Type": "Race", "Name": name,
        "StartDate": start, "EndDate": end, "GmtOffset": offset, "Path": path,
    }


class FakeLivetiming:
    """Stands in for live timing: endpoint -> payload or exception."""

    def __init__(self):
        self.responses = {
            "2026/Index.json": LIVETIMING_INDEX,
            "SessionInfo.json": _info(11420, "Race", VEGAS + "2026-11-21_Race/", "Finalised", "Complete",
                                      "2026-11-21T20:00:00", "2026-11-21T22:05:00"),
            VEGAS + "2026-11-20_Qualifying/SessionInfo.json": _info(
                11416, "Qualifying", VEGAS + "2026-11-20_Qualifying/", "Finalised", "Complete",
                "2026-11-20T20:00:00", "2026-11-20T21:00:00"),
        }
        self.calls = []

    def __call__(self, endpoint):
        self.calls.append(endpoint)
        value = self.responses.get(endpoint)
        if value is None:
            with sch._quiet():
                raise InvalidEndpointError(f"Endpoint not found: {endpoint}")
        if isinstance(value, Exception):
            raise value
        return value


@pytest.fixture
def live(monkeypatch):
    sch._cache.clear()
    sch._warned.clear()
    fake = FakeLivetiming()
    monkeypatch.setattr(sch, "_livetiming_json", fake)

    def query():
        q = MagicMock()
        def season(year):
            s = MagicMock()
            s.get_races.return_value.data.races = JOLPICA if year == 2026 else []
            return s
        q.season.side_effect = season
        return q
    client = MagicMock()
    client.query.side_effect = query
    monkeypatch.setattr(sch, "jolpica_client", client)
    yield fake
    sch._cache.clear()


def t(text):
    return datetime.fromisoformat(text).replace(tzinfo=UTC)


# --------------------------------------------------------------------------- calendar

def test_meetings_merge_sources(live):
    testing = livef1.next_meeting(t("2026-02-01T00:00:00"))
    vegas = livef1.next_meeting(t("2026-11-01T00:00:00"))
    qatar = livef1.next_meeting(t("2026-11-25T00:00:00"))

    assert testing.name == "Pre-Season Testing" and testing.round is None and testing.race is None

    # live timing wins once it lists the meeting: keys, paths, real end, offset
    assert (vegas.name, vegas.round, vegas.key) == ("Las Vegas Grand Prix", 21, 1300)
    assert vegas.official_name == "FORMULA 1 LAS VEGAS GRAND PRIX 2026"
    race = vegas.race
    assert race.key == 11420 and race.listed and not race.end_estimated
    assert race.start == t("2026-11-22T04:00:00") and race.end == t("2026-11-22T06:05:00")
    assert race.start_local.hour == 20 and race.gmt_offset == timedelta(hours=-8)

    # Jolpica only: estimated ends, nothing listed yet
    assert [s.name for s in qatar.sessions] == ["Practice 1", "Sprint Qualifying", "Sprint", "Qualifying", "Race"]
    assert all(not s.listed and s.end_estimated for s in qatar.sessions)
    assert qatar.key is None and qatar.round == 22
    sq = qatar.session("Sprint Qualifying")
    assert sq.end - sq.start == timedelta(minutes=45)
    assert qatar.race.end - qatar.race.start == timedelta(hours=2)


def test_jolpica_only_without_account(live):
    live.responses["2026/Index.json"] = AuthenticationError("no account")
    m = livef1.next_meeting(t("2026-02-01T00:00:00"))
    assert m.name == "Las Vegas Grand Prix"  # testing is only known to live timing
    assert not any(s.listed for s in m.sessions)


def test_meeting_matched_by_session_time_when_names_differ(live):
    live.responses["2026/Index.json"] = {"Meetings": [dict(LIVETIMING_INDEX["Meetings"][1], Name="Something Else")]}
    vegas = livef1.next_meeting(t("2026-11-01T00:00:00"))
    assert (vegas.name, vegas.key, vegas.round) == ("Las Vegas Grand Prix", 1300, 21)


def test_next_and_previous_session(live):
    during_fp1 = t("2026-11-27T14:00:00")
    s = livef1.next_session(now=during_fp1)
    assert (s.meeting, s.name) == ("Qatar Grand Prix", "Practice 1") and s.is_live(during_fp1)
    assert livef1.next_session(now=t("2026-11-27T14:31:00")).name == "Sprint Qualifying"
    assert livef1.next_session("Race", now=during_fp1).meeting == "Qatar Grand Prix"
    assert livef1.next_session(["Sprint", "Qualifying"], now=during_fp1).name == "Sprint"  # names match exactly
    assert livef1.next_session("practice", now=t("2026-11-23T00:00:00")).name == "Practice 1"

    prev = livef1.previous_session(now=during_fp1)
    assert (prev.meeting, prev.name) == ("Las Vegas Grand Prix", "Race")
    assert livef1.previous_session("Qualifying", now=during_fp1).key == 11416
    assert livef1.previous_session(now=t("2026-01-01T00:00:00")) is None
    assert livef1.next_session(now=t("2026-12-31T00:00:00")) is None


def test_next_and_previous_meeting(live):
    assert livef1.next_meeting(t("2026-11-22T05:00:00")).name == "Las Vegas Grand Prix"  # race still running
    assert livef1.next_meeting(t("2026-11-22T07:00:00")).name == "Qatar Grand Prix"
    assert livef1.previous_meeting(t("2026-11-22T05:00:00")).name == "Pre-Season Testing"
    assert livef1.previous_meeting(t("2026-11-22T07:00:00")).name == "Las Vegas Grand Prix"
    assert livef1.next_meeting(t("2026-12-01T00:00:00")) is None
    assert livef1.previous_meeting(t("2026-12-01T00:00:00")).name == "Qatar Grand Prix"


def test_now_accepts_strings_and_naive(live):
    assert sch._now("2026-11-27T14:00Z") == t("2026-11-27T14:00:00")
    assert sch._now(datetime(2026, 11, 27, 14)) == t("2026-11-27T14:00:00")
    assert sch._now(pd.Timestamp("2026-11-27T17:00", tz="Europe/Istanbul")) == t("2026-11-27T14:00:00")


def test_calendar_is_cached(live):
    livef1.next_session(now=t("2026-11-27T14:00:00"))
    livef1.previous_session(now=t("2026-11-27T14:00:00"))
    assert live.calls.count("2026/Index.json") == 1
    livef1.next_session(now=t("2026-11-27T14:00:00"), refresh=True)
    assert live.calls.count("2026/Index.json") == 2


# --------------------------------------------------------------------------- status

def test_session_status_flags():
    base = dict(key=1, name="Race", meeting="M", path=None, start=None, end=None)
    st = lambda ss, a: sch.SessionStatus(session_status=ss, archive_status=a, **base)
    assert not st("Inactive", "Complete").is_data_available
    assert st("Started", "Generating").is_live
    assert st("Aborted", "Complete").is_live and not st("Aborted", "Complete").is_data_available
    assert st("Finished", "Generating").is_finished and not st("Finished", "Generating").is_data_available
    assert st("Finalised", "Complete").is_data_available


def test_status_lookup(live):
    now = t("2026-11-25T00:00:00")
    race = livef1.previous_session(now=now)
    # the session live timing shows comes from the public file, no per-session request
    assert race.status().session_status == "Finalised"
    assert not any(c.endswith("2026-11-21_Race/SessionInfo.json") for c in live.calls)
    # any other listed session: its own SessionInfo.json
    assert livef1.previous_session("Qualifying", now=now).status().key == 11416
    # listed, nothing published
    assert livef1.previous_session("Practice 1", now=now).status() is None
    # not listed and not the one live timing shows
    assert livef1.next_session("Race", now=now).status() is None


def test_status_of_unlisted_session_live_timing_shows(live):
    live.responses["SessionInfo.json"] = _info(
        11421, "Practice 1", "2026/Q/P1/", "Started", "Generating",
        "2026-11-27T16:30:00", "2026-11-27T17:30:00", meeting="Qatar Grand Prix", offset="03:00:00")
    status = livef1.next_session(now=t("2026-11-27T13:00:00")).status()
    assert status.key == 11421 and status.is_live


def test_status_needs_account_for_other_sessions(live):
    live.responses[VEGAS + "2026-11-20_Qualifying/SessionInfo.json"] = AuthenticationError("no account")
    with pytest.raises(AuthenticationError):
        livef1.previous_session("Qualifying", now=t("2026-11-25T00:00:00")).status()


def test_load_needs_listing(live):
    with pytest.raises(LiveF1Error):
        livef1.next_session("Race", now=t("2026-11-25T00:00:00")).load()
