# Changelog

All notable changes to LiveF1 will be documented in this file.

## [Unreleased]

### Added

- Default analysis tables, built with the session's own table system (pandas backend; skipped with Polars):
  - Silver: `driverInfo` (driver display fields, `TeamColour` with `#`), `enrichedLaps` (`laps` plus `Stint`, `LapTimeSeconds`, `LapTrackStatus`, `IsGreen`, `IsValid`), `trackEvents` (SC / VSC / red flag windows with start and end time and lap) and `sessionSchedule` (the meeting's sessions in UTC and track-local time).
  - Gold: `ValidLaps`, `FastestLaps`, `LapTimeStats`, `BestSectors`, `Stints`, `FuelCorrectedLaps`, `LapOneStart` and `DriveCharacter`. `session.generate(gold=True, tables=[...])` builds the requested tables and everything they depend on.
- `livef1.analysis`: the functions behind those tables, with parameters, plus analyses that compare chosen drivers (`gap_between_drivers`, `track_region_times`, `track_dominance`) and `rotate_circuit` for the circuit map.
- `Session.get_lap_telemetry(pairs)`: car telemetry of chosen `(DriverNo, LapNo)` laps.
- `Circuit.corners` (number, name, distance in metres, X, Y, angle) and `Circuit.load_circuit_data()`; `Circuit.corners` and `Circuit.track_regions` load the circuit layout on first access.
- `livef1.configure(fuel_correction_per_lap=..., lap_one_distances=...)` sets the defaults of `FuelCorrectedLaps` and `LapOneStart`.

- Logging that adapts to where LiveF1 runs:
  - Terminals get coloured lines and progress bars for topic downloads and table builds.
  - Notebooks get coloured lines; `INFO` goes to stdout, so it is not shown in the red stderr box, and warnings and errors go to stderr. Progress bars are widgets when `ipywidgets` is installed.
  - In AWS Lambda and Google Cloud Functions/Run, records go to the platform's log handler, so Lambda adds the request id and applies `AWS_LAMBDA_LOG_FORMAT` and `AWS_LAMBDA_LOG_LEVEL`. Without such a handler, each record is one line (a traceback stays one CloudWatch event).
  - Piped output gets plain lines.
- New `livef1.configure()` options:
  - `log_style`: `"auto"`, `"pretty"`, `"plain"` or `"json"`; also settable with the `LIVEF1_LOG_STYLE` environment variable. `NO_COLOR` and `FORCE_COLOR` are honoured.
  - `progress`: turns the progress bars on or off.
  - `log_propagate`: hands LiveF1's records to the application's own logging setup.
- `Session.catalog()`: every table of the session as a DataFrame (bronze topics, silver and gold tables, results), with whether it is built, row and column counts, sources, how to access it and a description. It also lists the default tables `generate()` has not built yet, for example the gold tables after `generate()` without `gold=True`.
- `log_style="json"` prints one JSON object per line. Records from `generate()` carry structured fields (`event`, `layer`, `table`, `rows`, `duration_ms`, `tables`, `failed`) that CloudWatch Logs Insights can query.

### Changed

- `Session.generate()` fetches the circuit layout only once per circuit.
- `Session.generate()` logs a few summary lines instead of one or two lines per table: the session, the topics downloaded, one line per layer with timings, and the tables built. Row counts and timings per table are logged at `DEBUG`.
- A table that fails to build is logged as one error line naming the table and the exception. The traceback is logged at `DEBUG` level, for gold tables too, which had none before.
- "The callback function for the SILVER table ... was set." is logged at `DEBUG` as "Registered silver/gold table ...". It was logged at `INFO` and named every table SILVER, including gold tables.
- `generate()` downloads `SessionData` and, when `laps` is built, `PitStopSeries` together with the other topics. Before, they were fetched separately later on, each with its own log line. A topic that a table fetches by itself while tables are building is logged at `DEBUG`, without a second progress bar.
- In notebooks without `ipywidgets`, a log line printed while the text progress bar is shown no longer lands at the end of the bar's line.
- The selected meeting and session are logged on one line (`Meeting: ...`, `Session: ...`).
- Loaded results, starting grid and standings are logged at `DEBUG`.
- `import livef1` silences only warnings raised from LiveF1's own modules. Before, it turned off all warnings in the process.
- Messages that LiveF1 wrote with `print()` now go through the logger: results-page scraping failures, meeting reloads, and the debug output of two parsers.

### Fixed

- The logging guide used `configure()` parameter names that do not exist (`file_path`, `stream_format`). It now uses `logging_file_path` and `logging_stream_format`.

## [1.4.1] - 2026-11-02

### Fixed

- Sessions whose data stream runs longer than a day (for example a suspended race resumed the next day) can be loaded. From the second day on, the stream keys have a day prefix (`1.02:03:04.567`); they were cut at 12 characters before, which failed parsing. Keys of any length are now read, and the Bronze `timestamp` column turns `D.HH:MM:SS.fff` into a duration of D days plus the time, with both the pandas and the Polars backends.
- A stream record that is not valid JSON raises `ParsingError` again.

### Changed

- The pandas Bronze `timestamp` column is `NaT` for a key it cannot parse, instead of failing the table.
- Replaced the deprecated `DataFrame.rename(..., inplace=True)` calls in the pandas Silver functions, which warn on pandas 3.1.

### Tests

- Added tests for stream keys longer than a day, an invalid stream record, and `timestamp` parsing with both backends.
- The CI test dependencies include `polars` and `pyarrow`, so the Polars backend tests run instead of being skipped.

## [1.4.0] - 2026-11-01

### Polars DataFrame backend

LiveF1 can now build every table of a session with **Polars** instead of pandas. Install the extra with `pip install "livef1[polars]"` and call `livef1.configure(dataframe_backend="polars")` before loading data. Bronze tables are then built directly from the parsed livetiming records as `polars.DataFrame`, the default Silver tables are built with Polars, and custom Silver and Gold tables receive Polars inputs. Nothing is converted between pandas and Polars. pandas stays the default, and pandas code keeps working as before.

On the 2026 British Grand Prix race, the Polars backend builds the Silver tables about 4.6x faster than pandas (0.8 s vs 3.7 s), with smaller tables. Both backends give the same tables. See the DataFrame Backend page in the documentation.

### Added

- Added the `dataframe_backend` option to `livef1.configure()` (`"pandas"` by default, or `"polars"`). It is the only way to choose the backend.
- A session uses the backend configured when it builds its first table and keeps it from then on; `Session.dataframe_backend` reports it (read-only).
- Added the `polars` extra (`polars>=2.0`, `pyarrow>=14.0`).
- Added `livef1.data_processing.backends`, `livef1.data_processing.bronze_polars` (Bronze tables, track regions and session times built with Polars) and `livef1.data_processing.silver_functions_polars` (Polars versions of the `laps`, `carTelemetry` and `raceControlMessages` tables).
- Added `examples/polars_silver_compare.py`, which builds a session with both backends, checks that the tables match, and reports time and memory.

### Changed

- A table function registered with `create_silver_table` / `create_gold_table` that returns a DataFrame of the other backend (for example a Polars DataFrame in a pandas session) now raises `TypeError`.
- The pandas `carTelemetry` table is built one driver at a time and keeps only the columns it outputs. Peak memory while generating fell from about 520 MB to under 100 MB on a race, and the table builds about 1.5x faster. The values, row order and types are unchanged; the index is now `0..n-1`.
- Generating `carTelemetry` and `raceControlMessages` no longer modifies the Bronze tables they read: `CarData.z` and `Position.z` keep their original `Utc` strings and get no `tag` column, and `RaceControlMessages` keeps its original `Category` values.

### Fixed

- Deleted laps (track limits) were never marked in the pandas `laps` table: `raceControlMessages` was generated first and overwrote the `Category` of the Bronze race control messages that `laps` reads. `IsDeleted` and `DeletionMessage` are now filled in.
- `Compound` and `TyreAge` were wrong for lap 1 (which has no `LapTime`) and the lap after it. A lap without a `LapTime` now ends where the driver's next lap starts.
- `carTelemetry` duplicated a sample when its timestamp matched two TimingData rows of the same driver. Each sample now appears once.
- `raceControlMessages` failed for the whole session when an `Other` message matched none of the classification rules; such messages are now `Category="Other"`, `Scope="Unclassified"`. A driver flag other than blue or black-and-white (or a flag with an unhandled scope) no longer fails the table either.

### Documentation

- Added a DataFrame Backend user guide page, and the Polars extra to the installation page.
- Documented the `raceControlMessages` default table and the custom table return type in the medallion architecture guide.
- Added the backend and Polars modules to the API reference.

### Tests

- Added tests for the backend option, native Polars Bronze tables, session times and track regions against pandas, custom tables with both backends, and race control messages parity.
- The integration test runs `generate()` with both backends.
- Added regression tests for unclassified race control messages.

## [1.3.0] - 2026-10-24

### F1TV Subscription

Formula 1 now asks for a signed-in F1 account with an active **F1TV subscription** before it will serve live timing data. Without that subscription, season indexes, session archives (timing, telemetry, weather), and the live stream are refused.

LiveF1 1.3.0 signs in for you. Call `livef1.login()`, or do nothing: the first refused request signs in on its own. Put your account email and password in a `.env` file as `F1_USERNAME` and `F1_PASSWORD`. LiveF1 saves the resulting token and reuses it until it expires, so you are not asked again on every run. See the Authentication section of the README, and the Authentication page in the documentation, for the full setup.

Calendar and championship data from Jolpica does not need an F1TV account. Timing, telemetry, and the real-time client do.

Formula 1 also shut down the old live connection. The real-time client now uses the current one. Callbacks you already wrote keep working.

### Added

- Added F1 account (F1TV) password authentication for livetiming.formula1.com in `livef1.auth`, with `livef1.login()` and `livef1.logout()`.
- Credentials are read from `F1_USERNAME` / `F1_PASSWORD` in the environment or a `.env` file; if missing, the user is prompted and the values are saved to `.env` after a successful sign-in.
- The subscription token is saved to `~/.livef1/f1tv_auth_token.json` and reused until it expires; `login()` accepts `force`, `save_token`, `token_path` and `env_path`.
- Added `auth_save_token`, `auth_token_path` and `auth_env_path` options to `livef1.configure()`.
- Added `AuthenticationError`.
- Added `LIVEF1_TOKEN_PATH` (environment or `.env`) to set the token path; `login(token_path=...)` saves the absolute path there so later runs reuse the token without passing it again.
- The default `.env` is the first one found in the working directory or its parents, so notebooks in subfolders use the project's `.env`.

### Changed

- `LivetimingF1adapters.get()` sends the token with every request and, on HTTP 401 (or 403 without a token), signs in once and retries.
- `RealF1Client` now uses SignalR Core (`/signalrcore`); the classic `/signalr` endpoint was retired and returns HTTP 401. It connects with the F1TV token (signing in via `livef1.login()` if needed), keeps the connection alive with pings, and reconnects with backoff when it drops. The callback API is unchanged.
- Added a minimal built-in SignalR Core client (`livef1.adapters.signalrcore`) and removed the vendored classic `signalr_aio` client.
- Requires `websockets>=14.0`.
- Packaging now includes only the `livef1` package.

### Documentation

- Added an Authentication section to the README and an Authentication user guide page.

### Tests

- Added mocked tests for the sign-in flow, token decoding and storage, `.env` handling, and the adapter retry.
- Added mocked tests for SignalR Core framing, handshake, subscribe, message dispatch, close, and the realtime sign-in retry.

## [1.2.11] - 2026-09-13

### Added

- Added `TABLE_OPTIONAL_REQUIREMENTS` and `optional_source_tables` on `create_silver_table` / `create_gold_table` so tables can generate when optional sources are missing (callbacks receive `None`).
- Added `DataLake._is_resolvable_source()` to decide whether an optional source is already in the lake or available as a livetiming topic.

### Changed

- Moved `track_regions` off `TABLE_REQUIREMENTS["carTelemetry"]` so silver telemetry still generates when circuit data is unavailable; `TrackRegion` is left empty in that case.

### Documentation

- Documented optional source tables in the medallion architecture user guide.

### Tests

- Added unit tests for optional requirements constants, source resolvability, optional refine-sources behavior, and silver-table callbacks receiving `None` for missing optional sources.

## [1.2.10] - 2026-09-06

### Fixed

- Hardened `add_track_status()` to convert `LapEndTime` to timedelta and skip status merging when lap end times are empty, avoiding merge failures.
- Fixed laps-table `LapStartTime` / `LapTime` handling by normalizing missing timedeltas and recalculating start times from previous lap end before attaching track status.
- Sorted the generated laps table by `DriverNo` and `LapNo` for stable output order.

## [1.2.9] - 2026-08-29

### Fixed

- Rewrote `add_track_status()` for the laps table to derive lap end times and merge track status at lap boundaries, producing more reliable `TrackStatus` values per lap.
- Fixed missing lap 1 `Position` values by backfilling from the first TimingData position per driver.
- Guarded `IntervalToPositionAhead` enrichment in car telemetry so it runs only when TimingData exposes `IntervalToPositionAhead_Value`.

## [1.2.8] - 2026-08-25

### Added

- Added `IntervalToPositionAhead` to silver car telemetry via `add_interval_to_position_ahead()`, merged from TimingData and included in the silver car telemetry column order.

### Changed

- Raised the minimum `pandas` dependency from `>=2.2.0` to `>=3.0.3` in `pyproject.toml`, `requirements.txt`, and `uv.lock`.
- Raised the minimum supported Python version from `>=3.10` to `>=3.11` (required by pandas 3.x).
- Added `ipykernel>=7.3.0` as a package dependency for notebook workflows.

## [1.2.7] - 2026-08-22

### Fixed

- Fixed a circular import in `helper.py` by lazily importing `LivetimingF1adapters` inside `get_data()` and `get_car_data_stream()`.
- Fixed logger tests for pytest 9.1+ by asserting LiveF1-owned handler references instead of scanning `logger.handlers` with `isinstance()`.

### Changed

- Moved `pycountry`, `pytz`, and `ZoneInfo` imports to the top of `helper.py`.
- Synced `requirements.txt` with `pyproject.toml` dependencies (BaseF1, pycountry, pytz, timezonefinder, tqdm, and version pins).

## [1.2.6] - 2026-08-18

### Fixed

- Fixed `Season.load()` to skip Jolpica driver, constructor, and standings fetches when Jolpica is unavailable, and to tolerate partial Jolpica failures without breaking season construction.
- Fixed `Season.drivers` defaulting to a dict instead of a list.
- Fixed `Session` Jolpica availability to resolve the meeting race row before checking session fields, and to respect `season.is_jolpica_available`.
- Fixed `jolpica_session_available_on_race()` returning safely when the race row is `None`.
- Fixed Jolpica-only meeting merge for Practice 3 and Qualifying start times (date/time fallbacks).
- Fixed `Country` lookup for Turkey by normalizing to `Türkiye` before pycountry resolution.
- Fixed `Meeting.set_sessions()` skipping session entries without a `Name`.
- Removed leftover debug `print` calls from silver table generation.

### Tests

- Added `test_models_season.py` to verify livetiming-only seasons do not call Jolpica during load.
- Updated test fixtures with explicit backend availability flags and a `mock_season_jolpica_loaders` helper for offline generate tests.
- Added a unit test for `jolpica_session_available_on_race(None, ...)`.

## [1.2.5] - 2026-08-13

### Fixed

- Raised bronze coordinate downcasting from `float16` to `float32` for `X`, `Y`, and `Z` to avoid precision loss in distance and track calculations.

### Changed

- Added `LapNo` to the bronze downcast map as `uint8`.

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
