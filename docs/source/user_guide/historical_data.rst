.. _historical_data:

Historical Data
==============

The LiveF1 package provides access to historical Formula 1 data through Session objects, which contain comprehensive race data including timing, telemetry, and other metrics.

Accessing Historical Data
------------------------

Direct Session Access
^^^^^^^^^^^^^^^

The most common way to access historical data is through sessions:

.. code-block:: python

    import livef1

    # Get specific session directly
    race = livef1.get_session(
        season=2024,
        meeting_identifier="Spa",  # Circuit/Location name
        session_identifier="Race"     # Session type
    )

.. note::
    You can also access data through Season and Meeting objects for broader data exploration:
    
    .. code-block:: python
        
        # Alternative: Browse through season/meeting structure
        season = livef1.get_season(2024)
        belgian_gp = livef1.get_meeting(season=2024, meeting_identifier="Spa")
        
        # View available sessions
        print(belgian_gp.sessions_table)

Working with Session Data
------------------------

Once you have a session object, you can access different types of data:

1. Raw Data Access
^^^^^^^^^^^^^^^

.. code-block:: python
  
    # Access specific data
    weather_data = race.get_data("WeatherData")
    car_data = race.get_data("CarData.z")

    display(weather_data.head())
    display(car_data.head())

.. rst-class:: sphx-glr-script-out

 .. code-block:: none

    |    |   SessionKey | timestamp    |   AirTemp |   Humidity |   Pressure |   Rainfall |   TrackTemp |   WindDirection |   WindSpeed |
    |---:|-------------:|:-------------|----------:|-----------:|-----------:|-----------:|------------:|----------------:|------------:|
    |  0 |         9574 | 00:00:14.052 |      21   |         52 |      978.1 |          0 |        42.1 |             217 |         0.5 |
    |  1 |         9574 | 00:01:14.050 |      20.6 |         53 |      978   |          0 |        42.1 |               0 |         1.1 |
    |  2 |         9574 | 00:02:14.047 |      20.6 |         52 |      978   |          0 |        42.2 |             284 |         0.7 |
    |  3 |         9574 | 00:03:14.053 |      20.7 |         51 |      978.1 |          0 |        42   |             244 |         1.4 |
    |  4 |         9574 | 00:04:14.057 |      20.7 |         51 |      978.1 |          0 |        41.1 |              13 |         1.2 |

    |    |   SessionKey | timestamp    | Utc                          |   DriverNo |   rpm |   speed |   n_gear |   throttle |   brake |   drs |
    |---:|-------------:|:-------------|:-----------------------------|-----------:|------:|--------:|---------:|-----------:|--------:|------:|
    |  0 |         9574 | 00:02:28.746 | 2024-07-28T12:11:06.7233441Z |          1 |     0 |       0 |        0 |          0 |       0 |     0 |
    |  1 |         9574 | 00:02:28.746 | 2024-07-28T12:11:06.7233441Z |          2 |     0 |       0 |        0 |          0 |       0 |     0 |
    |  2 |         9574 | 00:02:28.746 | 2024-07-28T12:11:06.7233441Z |          3 |     0 |       0 |        0 |          0 |       0 |     0 |
    |  3 |         9574 | 00:02:28.746 | 2024-07-28T12:11:06.7233441Z |          4 |     0 |       0 |        0 |          0 |       0 |     0 |
    |  4 |         9574 | 00:02:28.746 | 2024-07-28T12:11:06.7233441Z |         10 |     0 |       0 |        0 |          0 |       0 |     0 |

.. seealso::
   For a complete list of available topics and their descriptions, see :ref:`data_topics`

2. Processed Data
^^^^^^^^^^^^^^^

Generate processed data tables using the medallion architecture:

.. code-block:: python

    # Generate silver and gold tables
    race.generate()
    
    # Access processed data
    laps = race.laps
    telemetry = race.carTelemetry

    display(laps.head())

.. rst-class:: sphx-glr-script-out

 .. code-block:: none

    |    |   lap_number | lap_time               | in_pit                 | pit_out   | sector1_time           | sector2_time           | sector3_time           | None   |   speed_I1 |   speed_I2 |   speed_FL |   speed_ST |   no_pits | lap_start_time         |   DriverNo | lap_start_date             |
    |---:|-------------:|:-----------------------|:-----------------------|:----------|:-----------------------|:-----------------------|:-----------------------|:-------|-----------:|-----------:|-----------:|-----------:|----------:|:-----------------------|-----------:|:---------------------------|
    |  0 |            1 | NaT                    | 0 days 00:17:07.661000 | NaT       | NaT                    | 0 days 00:00:48.663000 | 0 days 00:00:29.571000 |        |        314 |        204 |            |        303 |         0 | NaT                    |         16 | 2024-07-28 13:03:52.742000 |
    |  1 |            2 | 0 days 00:01:50.240000 | NaT                    | NaT       | 0 days 00:00:31.831000 | 0 days 00:00:48.675000 | 0 days 00:00:29.734000 |        |        303 |        203 |        219 |            |         0 | 0 days 00:57:07.067000 |         16 | 2024-07-28 13:05:45.045000 |
    |  2 |            3 | 0 days 00:01:50.519000 | NaT                    | NaT       | 0 days 00:00:31.833000 | 0 days 00:00:49.132000 | 0 days 00:00:29.554000 |        |        311 |        202 |        215 |        304 |         0 | 0 days 00:58:57.307000 |         16 | 2024-07-28 13:07:35.285000 |
    |  3 |            4 | 0 days 00:01:49.796000 | NaT                    | NaT       | 0 days 00:00:31.592000 | 0 days 00:00:48.778000 | 0 days 00:00:29.426000 |        |        312 |        201 |        217 |        309 |         0 | 0 days 01:00:47.870000 |         16 | 2024-07-28 13:09:25.848000 |
    |  4 |            5 | 0 days 00:01:49.494000 | NaT                    | NaT       | 0 days 00:00:31.394000 | 0 days 00:00:48.729000 | 0 days 00:00:29.371000 |        |        313 |        197 |        217 |        311 |         0 | 0 days 01:02:37.721000 |         16 | 2024-07-28 13:11:15.699000 |


Example: Complete Historical Data Analysis
----------------------------------------

Here's a complete example showing how to access and analyze historical race data:

.. code-block:: python

    import livef1
    
    # Get a specific race session
    race = livef1.get_session(
        season=2023,
        meeting_identifier="Monaco",
        session_identifier="Race"
    )
    
    # Generate processed data
    race.generate()
    
    # Get lap times and telemetry
    laps_data = race.laps
    telemetry = race.carTelemetry
    
    # Analyze fastest laps
    fastest_laps = laps_data.sort_values('LapTime').groupby('DriverNumber').first()
    print("Fastest laps by driver:\n****************")
    print(fastest_laps[['LapTime', 'LapNumber']])

.. rst-class:: sphx-glr-script-out

 .. code-block:: none

    Fastest laps by driver:
    ****************
    |   DriverNo | lap_time               |   lap_number |
    |-----------:|:-----------------------|-------------:|
    |          1 | 0 days 00:01:46.128000 |           32 |
    |         10 | 0 days 00:01:47.418000 |           30 |
    |         11 | 0 days 00:01:44.701000 |           44 |
    |         14 | 0 days 00:01:48.051000 |           42 |
    |         16 | 0 days 00:01:47.013000 |           33 |
    |         18 | 0 days 00:01:48.105000 |           44 |
    |          2 | 0 days 00:01:47.490000 |           43 |
    |         20 | 0 days 00:01:47.848000 |           44 |
    |         22 | 0 days 00:01:47.969000 |           44 |
    |         23 | 0 days 00:01:47.996000 |           44 |
    |         24 | 0 days 00:01:52.099000 |            2 |
    |         27 | 0 days 00:01:48.954000 |           44 |
    |          3 | 0 days 00:01:47.435000 |           37 |
    |         31 | 0 days 00:01:46.957000 |           43 |
    |          4 | 0 days 00:01:45.563000 |           31 |
    |         44 | 0 days 00:01:46.653000 |           33 |
    |         55 | 0 days 00:01:46.364000 |           44 |
    |         63 | 0 days 00:01:47.113000 |           44 |
    |         77 | 0 days 00:01:47.019000 |           37 |
    |         81 | 0 days 00:01:45.840000 |           32 |

.. Parallel Data Loading
.. -------------------

.. When working with multiple data topics, LiveF1 supports parallel data loading to improve performance. This is especially useful when retrieving multiple large datasets simultaneously. For best results, consider grouping related topics together, monitor memory usage when loading multiple topics in parallel, implement proper error handling for parallel requests, and handle partial failures gracefully. It's also recommended to use parallel loading only when retrieving multiple large datasets, as the overhead of parallelization may outweigh the benefits for small datasets.

.. Basic Usage
.. ^^^^^^^^^^

.. .. code-block:: python

..     # Load multiple topics in parallel (default behavior)
..     data = session.get_data(
..         ["CarData.z", "Position.z", "SessionStatus"]
..     )

..     # Load topics sequentially (parallel disabled)
..     data = session.get_data(
..         ["CarData.z", "Position.z", "SessionStatus"], 
..         parallel=False
..     )