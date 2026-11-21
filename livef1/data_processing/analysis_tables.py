"""
Default analysis tables of a session (pandas backend).

Silver tables (cheap, one row per entity):

- ``driverInfo``: driver display fields.
- ``enrichedLaps``: silver ``laps`` plus ``Stint``, ``LapTimeSeconds``,
  ``LapTrackStatus``, ``IsGreen`` and ``IsValid``.
- ``trackEvents``: safety car, VSC and red flag windows.
- ``sessionSchedule``: the meeting's sessions in UTC and track-local time.

Gold tables (aggregates with default parameters):

- ``ValidLaps``, ``FastestLaps``, ``LapTimeStats``, ``BestSectors``, ``Stints``,
  ``FuelCorrectedLaps``, ``LapOneStart``, ``DriveCharacter``.

Each table function receives its source tables (and the session when
``include_session`` is set) and only calls :mod:`livef1.analysis`; use those
functions directly for other parameters. Defaults that can be changed for the
generated tables are set with :func:`livef1.configure`
(``fuel_correction_per_lap``, ``lap_one_distances``).
"""
from ..config import _settings
from .. import analysis


def _setting(name, default):
    value = _settings.get(name)
    return default if value is None else value


# --- Silver ---------------------------------------------------------------

def generate_driver_info_table(session):
    return analysis.driver_info(getattr(session, "drivers", None))


def generate_enriched_laps_table(laps, track_status):
    return analysis.enrich_laps(laps, track_status)


def generate_track_events_table(session, track_status, laps):
    return analysis.track_events(track_status, laps, getattr(session, "first_datetime", None))


def generate_session_schedule_table(session):
    meeting = getattr(session, "meeting", None)
    return analysis.session_schedule(getattr(meeting, "meeting_table", None))


# --- Gold -----------------------------------------------------------------

def generate_valid_laps_table(enriched_laps):
    return analysis.valid_laps(enriched_laps)


def generate_fastest_laps_table(valid_laps, driver_info):
    return analysis.fastest_laps(valid_laps, driver_info)


def generate_laptime_stats_table(valid_laps, driver_info):
    return analysis.laptime_stats(valid_laps, driver_info)


def generate_best_sectors_table(laps, driver_info):
    return analysis.best_sectors(laps, driver_info)


def generate_stints_table(enriched_laps, driver_info):
    return analysis.stints(enriched_laps, driver_info)


def generate_fuel_corrected_laps_table(enriched_laps):
    k = _setting("fuel_correction_per_lap", analysis.DEFAULT_FUEL_CORRECTION_PER_LAP)
    return analysis.fuel_corrected_laps(enriched_laps, correction_per_lap=k)


def generate_lap_one_start_table(session, car_telemetry, laps, driver_info):
    distances = _setting("lap_one_distances", analysis.DEFAULT_LAP_ONE_DISTANCES)
    grid = getattr(session, "startingGrid", None)
    return analysis.lap_one_start(car_telemetry, laps, grid=grid, distances=distances, driver_info=driver_info)


def generate_drive_character_table(fastest_laps, car_telemetry, driver_info):
    best_lap_tel = analysis.select_lap_telemetry(car_telemetry, fastest_laps[["DriverNo", "LapNo"]])
    return analysis.drive_character(best_lap_tel, driver_info=driver_info)


# --- Registry -------------------------------------------------------------
# name -> (function, required sources, optional sources, include_session)

ANALYSIS_SILVER_TABLES = {
    "driverInfo": (generate_driver_info_table, [], [], True),
    "enrichedLaps": (generate_enriched_laps_table, ["laps", "TrackStatus"], [], False),
    "trackEvents": (generate_track_events_table, ["TrackStatus", "laps"], [], True),
    "sessionSchedule": (generate_session_schedule_table, [], [], True),
}

ANALYSIS_GOLD_TABLES = {
    "ValidLaps": (generate_valid_laps_table, ["enrichedLaps"], [], False),
    "FastestLaps": (generate_fastest_laps_table, ["ValidLaps", "driverInfo"], [], False),
    "LapTimeStats": (generate_laptime_stats_table, ["ValidLaps", "driverInfo"], [], False),
    "BestSectors": (generate_best_sectors_table, ["laps", "driverInfo"], [], False),
    "Stints": (generate_stints_table, ["enrichedLaps", "driverInfo"], [], False),
    "FuelCorrectedLaps": (generate_fuel_corrected_laps_table, ["enrichedLaps"], [], False),
    "LapOneStart": (generate_lap_one_start_table, ["carTelemetry", "laps", "driverInfo"], [], True),
    "DriveCharacter": (generate_drive_character_table, ["FastestLaps", "carTelemetry", "driverInfo"], [], False),
}
