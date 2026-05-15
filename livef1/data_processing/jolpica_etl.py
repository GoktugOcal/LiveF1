from livef1.models.constructor import Constructor, _jolpica_constructor_dict


def _resolve_constructor(season_obj, ctor_raw: dict) -> Constructor:
    """Return Constructor from registry or build from Jolpica nested dict."""
    if ctor_raw is None:
        return None
    cid = ctor_raw.get("constructorId")
    if cid and getattr(season_obj, "constructors", None) and cid in season_obj.constructors:
        return season_obj.constructors[cid]
    return Constructor(**_jolpica_constructor_dict(ctor_raw))


def parse_driver_standings(season_obj, data):
    """
    Turn Jolpica driver standing rows into dicts keyed like the API payload.

    Each row includes ``Driver`` (from ``season_obj.drivers`` where possible),
    ``Constructor`` (same for constructors registry), ``position``, ``points``, ``wins``.

    Previous versions exposed team name via ``Constructors``; use ``Constructor`` instead.
    """
    driver_standings = []
    for driver_standing in data:
        key = driver_standing["Driver"]["permanentNumber"] or driver_standing["Driver"]["driverId"]
        driver = season_obj.drivers[key]
        constructors = driver_standing.get("Constructors") or []
        ctor_raw = constructors[0] if constructors else None
        row = {
            "position": driver_standing["position"],
            "points": driver_standing["points"],
            "wins": driver_standing["wins"],
            "Driver": driver,
            "Constructor": _resolve_constructor(season_obj, ctor_raw),
        }
        driver_standings.append(row)

    return driver_standings


def parse_constructor_standings(season_obj, data):
    """Parse Jolpica ``ConstructorStandings`` rows; each row includes a ``Constructor`` instance."""
    constructor_standings = []
    for row in data:
        ctor_raw = row.get("Constructor")
        constructor_standings.append(
            {
                "position": row["position"],
                "points": row["points"],
                "wins": row["wins"],
                "Constructor": _resolve_constructor(season_obj, ctor_raw),
            }
        )
    return constructor_standings
