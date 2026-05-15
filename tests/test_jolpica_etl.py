"""Tests for livef1.data_processing.jolpica_etl."""
import pytest

from livef1.models.constructor import Constructor
from livef1.models.driver import Driver
from livef1.data_processing.jolpica_etl import (
    parse_constructor_standings,
    parse_driver_standings,
)


@pytest.fixture
def mock_season():
    class SeasonLike:
        pass

    s = SeasonLike()
    s.drivers = {"1": Driver(id="jd", RacingNumber="1", Tla="JD", FirstName="John", LastName="Doe")}
    s.constructors = {
        "alfa": Constructor(id="alfa", Name="Alfa Romeo", Nationality="Swiss", wiki=None),
    }
    return s


def test_parse_driver_standings_uses_constructor_from_registry(mock_season):
    data = [
        {
            "position": "1",
            "points": "25",
            "wins": "1",
            "Driver": {
                "driverId": "jd",
                "permanentNumber": "1",
                "code": "JD",
            },
            "Constructors": [
                {"constructorId": "alfa", "name": "Alfa Romeo", "nationality": "Swiss", "url": "http://wiki"}
            ],
        }
    ]
    rows = parse_driver_standings(mock_season, data)
    assert len(rows) == 1
    assert rows[0]["Driver"] is mock_season.drivers["1"]
    assert rows[0]["Constructor"] is mock_season.constructors["alfa"]
    assert rows[0]["position"] == "1"


def test_parse_driver_standings_synthesizes_missing_constructor(mock_season):
    data = [
        {
            "position": "2",
            "points": "18",
            "wins": "0",
            "Driver": {
                "driverId": "jd",
                "permanentNumber": "1",
                "code": "JD",
            },
            "Constructors": [
                {
                    "constructorId": "other_team",
                    "name": "Other",
                    "nationality": "Moon",
                    "url": "http://example.com",
                }
            ],
        }
    ]
    rows = parse_driver_standings(mock_season, data)
    assert isinstance(rows[0]["Constructor"], Constructor)
    assert rows[0]["Constructor"].id == "other_team"
    assert rows[0]["Constructor"].Name == "Other"


def test_parse_constructor_standings_registry_and_fallback(mock_season):
    registry_rows = [
        {
            "position": "10",
            "points": "0",
            "wins": "0",
            "Constructor": {"constructorId": "alfa", "name": "Alfa Romeo", "nationality": "Swiss"},
        }
    ]
    out_reg = parse_constructor_standings(mock_season, registry_rows)
    assert out_reg[0]["Constructor"] is mock_season.constructors["alfa"]

    fallback_rows = [
        {
            "position": "1",
            "points": "100",
            "wins": "5",
            "Constructor": {
                "constructorId": "zeta",
                "name": "Zeta GP",
                "nationality": "Unknown",
                "url": "http://test",
            },
        }
    ]
    out_fb = parse_constructor_standings(mock_season, fallback_rows)
    assert out_fb[0]["Constructor"].id == "zeta"
    assert out_fb[0]["Constructor"].Name == "Zeta GP"
