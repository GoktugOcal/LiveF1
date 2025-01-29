********************************
Quick Start
********************************

Once LiveF1 is installed, you can start using it to fetch real-time or historical F1 data.

Import the library
-------------------

Start by importing LiveF1:

.. code-block:: python

   import livef1 as livef1

Get a season object with its meetings and sessions
-------------------

The get_season function in the livef1 package is used to retrieve detailed information about a Formula 1 season. This includes an overview of the meetings (Grand Prix events) and their respective sessions.

.. code-block:: python

   import livef1 as livef1
   season = livef1.get_season(season=2021)
   print(season)

.. rst-class:: sphx-glr-script-out

 .. code-block:: none

   |   meeting_key |   season_year | meeting_code   |   meeting_number | meeting_location   | meeting_offname                            | meeting_name       |   meeting_country_key | meeting_country_code   | meeting_country_name   |   meeting_circuit_key | meeting_circuit_shortname   |   session_key | session_type   | session_name   | session_startDate   | session_endDate     | gmtoffset   | path                                                      |
   |--------------:|--------------:|:---------------|-----------------:|:-------------------|:-------------------------------------------|:-------------------|----------------------:|:-----------------------|:-----------------------|----------------------:|:----------------------------|--------------:|:---------------|:---------------|:--------------------|:--------------------|:------------|:----------------------------------------------------------|
   |          1064 |          2021 | BRN0104        |                1 | Sakhir             | FORMULA 1 GULF AIR BAHRAIN GRAND PRIX 2021 | Bahrain Grand Prix |                    36 | BRN                    | Bahrain                |                    63 | Sakhir                      |          6210 | Practice 1     | Practice 1     | 2021-03-26 14:30:00 | 2021-03-26 15:30:00 | 03:00:00    | 2021/2021-03-28_Bahrain_Grand_Prix/2021-03-26_Practice_1/ |
   |          1064 |          2021 | BRN0104        |                1 | Sakhir             | FORMULA 1 GULF AIR BAHRAIN GRAND PRIX 2021 | Bahrain Grand Prix |                    36 | BRN                    | Bahrain                |                    63 | Sakhir                      |          6211 | Practice 2     | Practice 2     | 2021-03-26 18:00:00 | 2021-03-26 19:00:00 | 03:00:00    | 2021/2021-03-28_Bahrain_Grand_Prix/2021-03-26_Practice_2/ |
   |          1064 |          2021 | BRN0104        |                1 | Sakhir             | FORMULA 1 GULF AIR BAHRAIN GRAND PRIX 2021 | Bahrain Grand Prix |                    36 | BRN                    | Bahrain                |                    63 | Sakhir                      |          6212 | Practice 3     | Practice 3     | 2021-03-27 15:00:00 | 2021-03-27 16:00:00 | 03:00:00    | 2021/2021-03-28_Bahrain_Grand_Prix/2021-03-27_Practice_3/ |
   |          1064 |          2021 | BRN0104        |                1 | Sakhir             | FORMULA 1 GULF AIR BAHRAIN GRAND PRIX 2021 | Bahrain Grand Prix |                    36 | BRN                    | Bahrain                |                    63 | Sakhir                      |          6213 | Qualifying     | Qualifying     | 2021-03-27 18:00:00 | 2021-03-27 19:00:00 | 03:00:00    | 2021/2021-03-28_Bahrain_Grand_Prix/2021-03-27_Qualifying/ |
   |          1064 |          2021 | BRN0104        |                1 | Sakhir             | FORMULA 1 GULF AIR BAHRAIN GRAND PRIX 2021 | Bahrain Grand Prix |                    36 | BRN                    | Bahrain                |                    63 | Sakhir                      |          6214 | Race           | Race           | 2021-03-28 18:00:00 | 2021-03-28 20:00:00 | 03:00:00    | 2021/2021-03-28_Bahrain_Grand_Prix/2021-03-28_Race/       |

The `season` object is an instance of the `Season` class, providing access to structured season data, including meetings and their corresponding sessions.

Once you retrieve a season, you can inspect its contents by printing the object. The output provides an overview of the meetings within the season, formatted as a table. Each row corresponds to a Grand Prix event, and the columns provide key details.

Get a meeting object and its sessions
-------------------

**Get a Meeting by Identifier.** The `get_meeting` function can retrieve a meeting by its identifier (e.g., a `location name`). Here’s how to use it:

.. code-block:: python

   import livef1 as livef1
   meeting = livef1.get_meeting(
      season=2024,
      meeting_key=1242
      )
   print(meeting)

**Get a Meeting by Key.** Alternatively, you can retrieve a meeting using its unique meeting key.

.. code-block:: python

   import livef1 as livef1
   meeting = livef1.get_meeting(
      season=2024, 
      meeting_identifier="Spa"
      )
   print(meeting)

.. rst-class:: sphx-glr-script-out

 .. code-block:: none

   |    |   Season Year | Meeting Location   | Session Type   | Meeting Code   |   Meeting Key |   Meeting Number | Meeting Offname                         | Meeting Name       |   Meeting Country Key | Meeting Country Code   | Meeting Country Name   |   Meeting Circuit Key | Meeting Circuit Shortname   |   Session Key | Session Name   | Session Startdate   | Session Enddate     | Gmtoffset   | Path                                                      |
   |---:|--------------:|:-------------------|:---------------|:---------------|--------------:|-----------------:|:----------------------------------------|:-------------------|----------------------:|:-----------------------|:-----------------------|----------------------:|:----------------------------|--------------:|:---------------|:--------------------|:--------------------|:------------|:----------------------------------------------------------|
   |  0 |          2024 | Spa-Francorchamps  | Practice 1     | BEL02012       |          1242 |               14 | FORMULA 1 ROLEX BELGIAN GRAND PRIX 2024 | Belgian Grand Prix |                    16 | BEL                    | Belgium                |                     7 | Spa-Francorchamps           |          9567 | Practice 1     | 2024-07-26 13:30:00 | 2024-07-26 14:30:00 | 02:00:00    | 2024/2024-07-28_Belgian_Grand_Prix/2024-07-26_Practice_1/ |
   |  1 |          2024 | Spa-Francorchamps  | Practice 2     | BEL02012       |          1242 |               14 | FORMULA 1 ROLEX BELGIAN GRAND PRIX 2024 | Belgian Grand Prix |                    16 | BEL                    | Belgium                |                     7 | Spa-Francorchamps           |          9568 | Practice 2     | 2024-07-26 17:00:00 | 2024-07-26 18:00:00 | 02:00:00    | 2024/2024-07-28_Belgian_Grand_Prix/2024-07-26_Practice_2/ |
   |  2 |          2024 | Spa-Francorchamps  | Practice 3     | BEL02012       |          1242 |               14 | FORMULA 1 ROLEX BELGIAN GRAND PRIX 2024 | Belgian Grand Prix |                    16 | BEL                    | Belgium                |                     7 | Spa-Francorchamps           |          9569 | Practice 3     | 2024-07-27 12:30:00 | 2024-07-27 13:30:00 | 02:00:00    | 2024/2024-07-28_Belgian_Grand_Prix/2024-07-27_Practice_3/ |
   |  3 |          2024 | Spa-Francorchamps  | Qualifying     | BEL02012       |          1242 |               14 | FORMULA 1 ROLEX BELGIAN GRAND PRIX 2024 | Belgian Grand Prix |                    16 | BEL                    | Belgium                |                     7 | Spa-Francorchamps           |          9570 | Qualifying     | 2024-07-27 16:00:00 | 2024-07-27 17:00:00 | 02:00:00    | 2024/2024-07-28_Belgian_Grand_Prix/2024-07-27_Qualifying/ |
   |  4 |          2024 | Spa-Francorchamps  | Race           | BEL02012       |          1242 |               14 | FORMULA 1 ROLEX BELGIAN GRAND PRIX 2024 | Belgian Grand Prix |                    16 | BEL                    | Belgium                |                     7 | Spa-Francorchamps           |          9574 | Race           | 2024-07-28 15:00:00 | 2024-07-28 17:00:00 | 02:00:00    | 2024/2024-07-28_Belgian_Grand_Prix/2024-07-28_Race/       |

The output provides a detailed table of the meeting’s sessions, with relevant details for each session.


Get session object and load data
-------------------

The `livef1` package provides an intuitive way to load session-specific data, such as telemetry, track conditions, and other statistical information. Follow the steps below to get started.

To begin, retrieve a session object for the desired Formula 1 event by specifying the season, meeting (e.g., Grand Prix location), and session type (e.g., Practice, Qualifying, Race):

.. code-block:: python

   import livef1
   session = livef1.get_session(
      season=2024,
      meeting_identifier="Spa",
      session_identifier="Race"
      )

The :class:`~Session` object acts as the gateway to all available data feeds for the specified session.

Use the `print_topic_names` method to explore the available data feeds for the session. Each feed provides specific information, such as live telemetry, session details, or track conditions:

.. code-block:: python

   session.print_topic_names()

.. rst-class:: sphx-glr-script-out

 .. code-block:: none
   :emphasize-lines: 11-12
   
   Session_Info : 
         Details about the current session.
   Archive_Status : 
            Status of archived session data.
   Track_Status : 
            Current conditions and status of the track.
   Session_Data : 
            Raw data for the ongoing session.
   Position : 
            Position data of cars.
   Car_Data : 
            Car sensor data.
   .
   .
   .

Each feed is identified by a unique name (e.g., Session_Info, Track_Status) and comes with a description to help you understand its purpose. This helps you identify the data most relevant to your analysis.

.. note::
   The data feeds is further explained in :ref:`data_topics` section.

Load specific data by name of data
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Once you’ve identified the desired data feed, you can load its contents using the `get_data` method. For example, to load car telemetry data:

.. code-block:: python

   data = session.get_data(dataName="Car_Data")
   print(data)

.. rst-class:: sphx-glr-script-out

 .. code-block:: none

   |    |   SessionKey | timestamp    | Utc                          |   DriverNo | Status   |   X |   Y |   Z |
   |---:|-------------:|:-------------|:-----------------------------|-----------:|:---------|----:|----:|----:|
   |  0 |         9590 | 00:00:30.209 | 2024-09-01T12:08:13.7879709Z |          1 | OnTrack  |   0 |   0 |   0 |
   |  1 |         9590 | 00:00:30.209 | 2024-09-01T12:08:13.7879709Z |          3 | OnTrack  |   0 |   0 |   0 |
   |  2 |         9590 | 00:00:30.209 | 2024-09-01T12:08:13.7879709Z |          4 | OnTrack  |   0 |   0 |   0 |
   |  3 |         9590 | 00:00:30.209 | 2024-09-01T12:08:13.7879709Z |         10 | OnTrack  |   0 |   0 |   0 |
   |  4 |         9590 | 00:00:30.209 | 2024-09-01T12:08:13.7879709Z |         11 | OnTrack  |   0 |   0 |   0 |

Load silver tables
^^^^^^^^^^^^^^^^^^

The `livef1` package follows the Medallion Architecture, which organizes data into different layers based on their level of refinement: Bronze, Silver, and Gold. The `generate` method in the `Session` class is used to create Silver tables from the raw data.

.. note::

   For more details on the Medallion Architecture, refer to the :ref:`medallion_architecture`.

To generate Silver tables, call the `generate` method:

.. code-block:: python

   session.generate(silver=True)

This method processes the raw data in the Bronze layer and creates cleaned and enriched tables in the Silver layer. The generated tables can then be accessed as attributes of the `Session` object. For example, to access the laps data:

.. code-block:: python

   laps_data = session.get_laps()
   print(laps_data)

.. rst-class:: sphx-glr-script-out

 .. code-block:: none

   |    |   lap_number | lap_time               | in_pit                 | pit_out   | sector1_time           | sector2_time           | sector3_time           | None   |   speed_I1 |   speed_I2 |   speed_FL |   speed_ST |   no_pits | lap_start_time         |   DriverNo | lap_start_date             |
   |---:|-------------:|:-----------------------|:-----------------------|:----------|:-----------------------|:-----------------------|:-----------------------|:-------|-----------:|-----------:|-----------:|-----------:|----------:|:-----------------------|-----------:|:---------------------------|
   |  0 |            1 | NaT                    | 0 days 00:17:07.661000 | NaT       | NaT                    | 0 days 00:00:48.663000 | 0 days 00:00:29.571000 |        |        314 |        204 |        219 |        303 |         0 | NaT                    |         16 | 2024-07-28 13:03:52.742000 |
   |  1 |            2 | 0 days 00:01:50.240000 | NaT                    | NaT       | 0 days 00:00:31.831000 | 0 days 00:00:48.675000 | 0 days 00:00:29.734000 |        |        303 |        203 |        215 |            |         0 | 0 days 00:57:07.067000 |         16 | 2024-07-28 13:05:45.045000 |
   |  2 |            3 | 0 days 00:01:50.519000 | NaT                    | NaT       | 0 days 00:00:31.833000 | 0 days 00:00:49.132000 | 0 days 00:00:29.554000 |        |        311 |        202 |        217 |        304 |         0 | 0 days 00:58:57.307000 |         16 | 2024-07-28 13:07:35.285000 |
   |  3 |            4 | 0 days 00:01:49.796000 | NaT                    | NaT       | 0 days 00:00:31.592000 | 0 days 00:00:48.778000 | 0 days 00:00:29.426000 |        |        312 |        201 |        217 |        309 |         0 | 0 days 01:00:47.870000 |         16 | 2024-07-28 13:09:25.848000 |
   |  4 |            5 | 0 days 00:01:49.494000 | NaT                    | NaT       | 0 days 00:00:31.394000 | 0 days 00:00:48.729000 | 0 days 00:00:29.371000 |        |        313 |        197 |        216 |        311 |         0 | 0 days 01:02:37.721000 |         16 | 2024-07-28 13:11:15.699000 |

The Silver tables provide high-quality data that is ready for analysis and reporting.

.. Example: Visualize Car Data
.. ------------------------------------

.. Once you have loaded the car data, you can visualize it to gain insights into the performance and behavior of a specific driver. In this example, we will visualize the car data for driver number 44.

.. First, load the car data using the `get_data` method:

.. .. code-block:: python

..    import pandas as pd
..    data = session.get_data(dataName="Car_Data")
..    df_car = pd.DataFrame(data.value)

.. Next, filter the data for driver number 44:

.. .. code-block:: python

..    driver_data = df_car[df_car['DriverNo'] == 44]

.. Finally, use a plotting library such as `matplotlib` to visualize the data. For example, to plot the X, Y, and Z coordinates of the car:

.. .. code-block:: python

..    import matplotlib.pyplot as plt

..    plt.figure(figsize=(10, 6))
..    plt.plot(driver_data['timestamp'], driver_data['X'], label='X Coordinate')
..    plt.plot(driver_data['timestamp'], driver_data['Y'], label='Y Coordinate')
..    plt.plot(driver_data['timestamp'], driver_data['Z'], label='Z Coordinate')
..    plt.xlabel('Timestamp')
..    plt.ylabel('Coordinate Value')
..    plt.title('Car Data for Driver No. 44')
..    plt.legend()
..    plt.show()

.. This will generate a plot showing the X, Y, and Z coordinates of the car for driver number 44 over time.

.. .. note::
..    You can customize the visualization further by adding more plots or using different visualization libraries.