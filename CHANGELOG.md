# Changelog

All notable changes to LiveF1 will be documented in this file.

## [1.2.4] - 2026-08-04

### Fixed

- Fixed selective `Session.generate(tables=...)` so silver/gold tables generate correctly when `tables` is omitted (previously required an explicit list).
- Fixed table generation to expand transitive silver/gold dependencies and topologically sort them before building, so dependent tables are generated in a valid order.

### Added

- Added `DataLake._expand_table_dependencies()` and `DataLake._topo_sort_tables()` helpers for dependency closure and ordered generation.
- Added unit tests covering lake dependency expansion and topological sorting.

## [1.2.3] - 2026-08-04

### Added

- Added package-level `livef1.configure()` (`livef1.config`) to set logging level, stream/file formats, and an optional file log path before execution. Designed to grow with non-logging settings later.
- Exported `configure` from the top-level `livef1` package alongside `set_log_level`.

### Changed

- File logging is now optional and **disabled by default** (console only), so LiveF1 works on read-only filesystems such as containerized Lambda. Enable with `livef1.configure(logging_file_path=...)`.
- Refactored the logger module around `configure_logging()` with reconfigurable stream and file handlers.

### Documentation

- Documented `livef1.configure()` in the API reference and rewrote the logging user guide for console-only defaults and optional file logging.

### Tests

- Added logger / `configure()` unit tests covering level changes, stream formatting, and optional file handlers.

## [1.2.2] - 2026-08-02

### Added

- Added bronze-table memory optimization via `downcast` and `categorize` helpers, with configurable downcast and categorical column maps in `constants`.
- Added `DataLake.clear()` / `clear_data()` and matching lake-level helpers to drop cached bronze, silver, and gold tables.
- Added optional `tables` argument to `Session.generate()` so callers can request a subset of silver or gold tables.

### Changed

- Stream logger format now includes the logger name (`%(name)s`).
- Car telemetry generation frees intermediate DataFrames earlier to reduce peak memory use.

## [1.2.1] - 2026-06-14

### Added

- Added Barcelona Grand Prix circuit key mapping in `circuits_key.csv`.

### Fixed

- Fixed `Session.get_driver()` raising errors when driver name or TLA fields are missing or `None`.

## [1.2.0] - 2026-05-16

Changes since `v1.1.107`.

### Added

- Added Jolpica F1 support through the new BaseF1-backed adapter, giving LiveF1 a second backend for seasons, race calendars, constructors, standings, and other Ergast-style structured data.
- Added merged season calendar support that combines Formula 1 Livetiming meetings with Jolpica races, enriches shared meetings with round, URL, and circuit metadata, and includes Jolpica-only rounds where Livetiming data is unavailable.
- Added synthetic session metadata for Jolpica-only meetings so practice, qualifying, sprint, sprint qualifying, and race sessions can still be represented in the LiveF1 object model.
- Added backend availability checks for seasons, meetings, and sessions, including helpers for detecting whether data is available from Livetiming, Jolpica, or both.
- Added constructor standings and driver standings parsing from Jolpica, with registry-backed `Driver` and `Constructor` objects.
- Added new `Constructor`, `Country`, and `Location` model classes, plus richer circuit location handling and timezone inference.
- Added `round` metadata to season and meeting tables.
- Added a `uv.lock` lockfile and a `.python-version` file for more reproducible local environments.

### Changed

- Bumped the package version from `1.1.107` to `1.2.0`.
- Raised the minimum supported Python version from `>=3.09` to `>=3.10`.
- Updated `list_seasons()` to use Jolpica season data.
- Updated `get_session()` so session data loads when either Livetiming or Jolpica data is available.
- Expanded package exports for new models and adapter symbols.
- Added new runtime dependencies: `basef1`, `pycountry`, `pytz`, `timezonefinder`, and `tqdm`.

### Documentation

- Added README documentation for the dual data-source model and the new Jolpica/BaseF1 integration.
- Added a user guide page explaining Livetiming vs Jolpica responsibilities, limitations, and provider notes.
- Updated API reference, data model, historical data, realtime data, installation, and topic documentation for the new backend behavior.
- Removed the active `sphinx-tabs` docs dependency.

### Tests

- Added unit tests for Livetiming and Jolpica availability helper behavior.
- Added unit tests for Jolpica standings ETL, including constructor registry reuse and fallback constructor creation.
- Updated existing adapter, API, and integration tests for the new backend-aware behavior.

### Compatibility Notes

- Python 3.9 is no longer supported by the package metadata.
- Driver standings rows now expose a singular `Constructor` object instead of the previous `Constructors`-style team field.
- Jolpica-backed or synthetic sessions may not expose the high-frequency Livetiming topics available for fully Livetiming-backed sessions.
