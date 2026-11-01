.. _dataframe_backend:

DataFrame Backend (pandas or Polars)
====================================

LiveF1 builds every table of a session's data lake, from the raw Bronze tables to
the Silver and Gold tables, with one DataFrame library: **pandas** (the default) or
**Polars**. Both backends produce the same tables with the same columns and values.
Polars is faster and uses less memory.

Installing Polars
-----------------

pandas is always installed. Polars is an optional dependency:

.. code-block:: bash

   pip install "livef1[polars]"

Choosing the backend
--------------------

Set the backend with :func:`livef1.configure` before loading data:

.. code-block:: python

   import livef1

   livef1.configure(dataframe_backend="polars")

   session = livef1.get_session(2026, "British", "Race")
   session.generate()

   session.laps                 # polars.DataFrame
   session.carTelemetry         # polars.DataFrame
   session.get_data("CarData.z")  # polars.DataFrame (Bronze)

``dataframe_backend`` accepts ``"pandas"`` (default) or ``"polars"``. It is only set
through ``livef1.configure()``: ``get_session()`` and ``Session`` do not take a backend
argument. An unknown name raises ``ValueError``, and choosing ``"polars"`` without
Polars installed raises ``ImportError`` with the install command.

What the backend changes
------------------------

With the Polars backend, nothing in the data lake is pandas and nothing is converted
between the two libraries:

- **Bronze** tables are built directly from the parsed livetiming records as
  ``polars.DataFrame``, with the same column names, number types and ``timestamp``
  parsing as the pandas tables.
- **Silver** default tables (``laps``, ``carTelemetry``, ``raceControlMessages``) are
  built by Polars implementations of the pandas silver functions
  (:mod:`livef1.data_processing.silver_functions_polars`).
- **Gold** and custom tables receive Polars source tables (see `Custom tables`_).
- ``session.get_data()``, ``session.get_laps()``, ``session.get_car_telemetry()`` and the
  table attributes such as ``session.laps`` return Polars DataFrames.

When the backend is applied
---------------------------

A session takes the configured backend when it builds its first table (usually when
it loads its first Bronze topic, or when ``generate()`` runs) and keeps it from then
on, so all of its tables share one format. Changing ``configure()`` later only affects
sessions that have not loaded any data yet:

.. code-block:: python

   livef1.configure(dataframe_backend="polars")
   race = livef1.get_session(2026, "British", "Race")
   race.get_data("TimingData")       # race is now a Polars session

   livef1.configure(dataframe_backend="pandas")
   quali = livef1.get_session(2026, "British", "Qualifying")
   quali.generate()                  # quali uses pandas

   race.dataframe_backend            # "polars"
   quali.dataframe_backend           # "pandas"

``session.dataframe_backend`` is read-only.

Custom tables
-------------

Tables registered with ``create_silver_table`` and ``create_gold_table`` receive their
source tables in the session's backend, and must return a DataFrame of the same
library. Returning the other library's DataFrame raises ``TypeError``; LiveF1 does not
convert it. Write the table function with the API of the backend you configure:

.. code-block:: python
   :caption: Example: a custom Silver table with the Polars backend

   import livef1
   import polars as pl

   livef1.configure(dataframe_backend="polars")
   session = livef1.get_session(2026, "British", "Race")

   @session.create_silver_table(table_name="FastestLaps", source_tables=["laps"])
   def fastest_laps(laps):
       return (
           laps.filter(~pl.col("IsDeleted"))
           .group_by("DriverNo")
           .agg(pl.col("LapTime").min())
           .sort("LapTime")
       )

   session.generate()
   print(session.FastestLaps.head(3))

The pandas examples in :ref:`registering_custom_tables` work unchanged with the
default pandas backend.

Differences between the backends
--------------------------------

The values are the same; a few representation details follow each library:

- **Types**: pandas categorical columns (for example ``DriverNo``, ``Compound``,
  ``CarStatus``) are plain strings in Polars, ``SessionKey`` is an integer, and time
  columns use Polars ``Duration`` and ``Datetime``. Polars DataFrames have no index.
- **Driver column**: the ``Driver`` column of ``laps`` holds LiveF1 ``Driver`` objects in
  both backends (a Polars ``Object`` column).
- **Track regions**: the ``Circuit`` model keeps its ``track_regions`` as a pandas
  DataFrame because a circuit is shared by sessions of either backend. The
  ``track_regions`` Bronze table of a session follows the session's backend.
- **TrackRegion boundaries**: a telemetry sample whose ``Distance`` falls exactly on a
  corner boundary can, very rarely, be labelled with the neighbouring region because
  of floating-point rounding (2 of about 840,000 samples in the 2026 British Grand
  Prix).

Performance
-----------

Measured on the 2026 British Grand Prix race on an Apple Silicon laptop, with the
raw data already downloaded:

.. list-table::
   :header-rows: 1
   :widths: 40 20 20 20

   * - Step
     - pandas
     - Polars
     - Speed-up
   * - Build Bronze tables from parsed records
     - 2.0 s
     - 1.3 s
     - 1.6x
   * - ``laps``
     - 1.4 s
     - 0.12 s
     - 11x
   * - ``carTelemetry``
     - 2.2 s
     - 0.65 s
     - 3.4x
   * - All Silver tables
     - 3.7 s
     - 0.8 s
     - 4.6x
   * - Size of the Bronze tables
     - 184 MB
     - 121 MB
     -
   * - Size of the Silver tables
     - 112 MB
     - 87 MB
     -
   * - Peak extra memory while generating
     - 45-97 MB
     - 58-61 MB
     -

To compare the two backends on any session, run the comparison script from the
repository:

.. code-block:: bash

   python examples/polars_silver_compare.py 2026 British Race

It builds the session with each backend, checks that the tables match, and prints
the timings and memory use.
