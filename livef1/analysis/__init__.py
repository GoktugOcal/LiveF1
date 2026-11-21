"""
Reusable F1 analyses on LiveF1 tables (pandas).

The default silver and gold analysis tables (``enrichedLaps``, ``ValidLaps``,
``FastestLaps`` ...) are built from these functions with default parameters; call
the functions directly for other parameters or for analyses that compare chosen
drivers, such as :func:`gap_between_drivers` or :func:`track_dominance`.

Examples
--------
>>> from livef1 import analysis
>>> session.generate(gold=True, tables=["FastestLaps"])
>>> pole, second = session.FastestLaps.DriverNo[:2]
>>> laps = session.FastestLaps[session.FastestLaps.DriverNo.isin([pole, second])]
>>> tel = session.get_lap_telemetry(laps)
>>> analysis.gap_between_drivers(tel, reference_driver=pole)
"""
from .laps import (
    TRACK_STATUS,
    GREEN_TRACK_STATUS_CODES,
    DEFAULT_FUEL_CORRECTION_PER_LAP,
    DEFAULT_IQR_FACTOR,
    lap_track_status,
    is_green,
    enrich_laps,
    remove_outliers,
    valid_laps,
    fastest_laps,
    laptime_stats,
    best_sectors,
    stints,
    fuel_corrected_laps,
    driver_info,
)
from .track import (
    TRACK_EVENT_CODES,
    track_events,
    track_events_by_type,
    corners_table,
    rotate_xy,
    rotate_circuit,
    assign_track_regions,
    track_region_times,
    track_dominance,
    gap_between_drivers,
)
from .telemetry import (
    DEFAULT_LAP_ONE_DISTANCES,
    select_lap_telemetry,
    drive_character,
    lap_one_start,
)
from .schedule import parse_gmt_offset, session_schedule

__all__ = [
    "TRACK_STATUS", "GREEN_TRACK_STATUS_CODES", "DEFAULT_FUEL_CORRECTION_PER_LAP", "DEFAULT_IQR_FACTOR",
    "TRACK_EVENT_CODES", "DEFAULT_LAP_ONE_DISTANCES",
    "lap_track_status", "is_green", "enrich_laps", "remove_outliers", "valid_laps", "fastest_laps",
    "laptime_stats", "best_sectors", "stints", "fuel_corrected_laps", "driver_info",
    "track_events", "track_events_by_type", "corners_table", "rotate_xy", "rotate_circuit",
    "assign_track_regions", "track_region_times", "track_dominance", "gap_between_drivers",
    "select_lap_telemetry", "drive_character", "lap_one_start",
    "parse_gmt_offset", "session_schedule",
]
