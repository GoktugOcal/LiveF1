**********************************
Accessing Data
**********************************

Accessing Data and Generating Lake Levels
==========================================

This section explains how to access data and generate different lake levels (bronze, silver, and gold) using the `Session` class.

Accessing Data
--------------

To access data for a specific session, you can use the `get_data` method. This method retrieves data from the data lake or loads it if not present.

Example:

.. code-block:: python

    session = Session(season=season, year=2023, meeting=meeting, key=1, name="Race", type="race")
    timing_data = session.get_data("Timing_Data")
    print(timing_data)

Generating Silver and Gold Tables
---------------------------------

To generate silver and gold tables, use the `generate` method. This method processes raw data and creates higher-level tables.

Example:

.. code-block:: python

    session.generate(silver=True, gold=False)  # Generate silver tables only
    session.generate(silver=True, gold=True)   # Generate both silver and gold tables (not implemented yet)

Accessing Generated Tables
--------------------------

After generating the tables, you can access them using the corresponding methods.

Example:

.. code-block:: python

    laps_data = session.laps
    car_telemetry_data = session.carTelemetry
    weather_data = session.get_weather()
    timing_data = session.get_timing()

    print(laps_data)
    print(car_telemetry_data)
    print(weather_data)
    print(timing_data)