"""Unit tests for Livetiming / Jolpica availability predicates in adapters.functions."""

import pytest

from livef1.adapters.functions import (
    livetiming_meeting_in_season_index,
    livetiming_session_in_season_index,
    jolpica_meeting_in_races,
    jolpica_session_available_on_race,
    _norm_schedule_str,
)


def _livetiming_payload():
    return {
        "Meetings": [
            {
                "Name": "Bahrain",
                "Sessions": [
                    {"Name": "Practice 1", "Type": "Practice", "Number": 1},
                    {"Name": "Qualifying", "Type": "Qualifying"},
                    {"Name": "Sprint", "Type": "Race", "Number": -1},
                    {"Name": "Race", "Type": "Race"},
                ],
            }
        ]
    }


def test_norm_schedule_str():
    assert _norm_schedule_str("  Bahrain  ") == "bahrain"
    assert _norm_schedule_str(None) == ""


def test_livetiming_meeting_in_season_index():
    p = _livetiming_payload()
    assert livetiming_meeting_in_season_index(p, "Bahrain") is True
    assert livetiming_meeting_in_season_index(p, "bahrain") is True
    assert livetiming_meeting_in_season_index(p, "Monaco") is False
    assert livetiming_meeting_in_season_index({}, "Bahrain") is False


def test_livetiming_meeting_in_season_index_dict_meetings():
    p = {"Meetings": {"gp1": {"Name": "Bahrain", "Sessions": []}}}
    assert livetiming_meeting_in_season_index(p, "Bahrain") is True


def test_livetiming_session_in_season_index_by_name():
    p = _livetiming_payload()
    assert livetiming_session_in_season_index(p, "Bahrain", "Practice 1", None, None) is True
    assert livetiming_session_in_season_index(p, "Bahrain", "Race", None, None) is True


def test_livetiming_session_in_season_index_by_type_number():
    p = _livetiming_payload()
    assert livetiming_session_in_season_index(p, "Bahrain", None, "Practice", 1) is True
    assert livetiming_session_in_season_index(p, "Bahrain", None, "Race", -1) is True
    assert livetiming_session_in_season_index(p, "Bahrain", None, "Practice", 2) is False


def test_livetiming_session_wrong_meeting():
    p = _livetiming_payload()
    assert livetiming_session_in_season_index(p, "Monaco", "Race", None, None) is False


class _FakeRace:
    def __init__(self, race_name: str, keys: frozenset):
        self.race_name = race_name
        self._keys = keys

    def to_dict(self):
        return {k: True for k in self._keys}


def test_jolpica_meeting_in_races():
    races = [_FakeRace("Bahrain", frozenset())]
    assert jolpica_meeting_in_races(races, "bahrain") is True
    assert jolpica_meeting_in_races(races, "Monaco") is False
    assert jolpica_meeting_in_races([], "Bahrain") is False


@pytest.mark.parametrize(
    "name,type_,num,keys,expected",
    [
        ("Race", "Race", None, frozenset(), True),
        ("Race", "Race", 99, frozenset(), True),
        ("Sprint", "Race", -1, frozenset({"Sprint"}), True),
        ("Sprint", "Race", -1, frozenset(), False),
        ("Qualifying", "Qualifying", None, frozenset({"Qualifying"}), True),
        ("Practice 1", "Practice", 1, frozenset({"FirstPractice"}), True),
        ("Practice 2", "Practice", 2, frozenset({"SecondPractice"}), True),
        ("Practice 3", "Practice", 3, frozenset({"ThirdPractice"}), True),
        (None, "Qualifying", -1, frozenset({"SprintQualifying"}), True),
        ("Sprint Qualifying", None, None, frozenset({"SprintQualifying"}), True),
    ],
)
def test_jolpica_session_available_on_race(name, type_, num, keys, expected):
    race = _FakeRace("Bahrain", keys)
    assert jolpica_session_available_on_race(race, name, type_, num) is expected


def test_jolpica_session_dict_race():
    class R:
        race_name = "Bahrain"

        def to_dict(self):
            return {"Qualifying": {}}

    assert jolpica_session_available_on_race(R(), "Qualifying", "Qualifying", None) is True
