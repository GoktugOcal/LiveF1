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

   >>> import livef1 as livef1
   >>> meeting = livef1.get_meeting(season=2024, meeting_identifier="Spa")
   >>> type(meeting)
   <class livef1.models.meeting.Meeting>
   >>> meeting
   |    |   Season Year | Meeting Location   | Session Type   | Meeting Code   |   Meeting Key |   Meeting Number | Meeting Offname                         | Meeting Name       |   Meeting Country Key | Meeting Country Code   | Meeting Country Name   |   Meeting Circuit Key | Meeting Circuit Shortname   |   Session Key | Session Name   | Session Startdate   | Session Enddate     | Gmtoffset   | Path                                                      |
   |---:|--------------:|:-------------------|:---------------|:---------------|--------------:|-----------------:|:----------------------------------------|:-------------------|----------------------:|:-----------------------|:-----------------------|----------------------:|:----------------------------|--------------:|:---------------|:--------------------|:--------------------|:------------|:----------------------------------------------------------|
   |  0 |          2024 | Spa-Francorchamps  | Practice 1     | BEL02012       |          1242 |               14 | FORMULA 1 ROLEX BELGIAN GRAND PRIX 2024 | Belgian Grand Prix |                    16 | BEL                    | Belgium                |                     7 | Spa-Francorchamps           |          9567 | Practice 1     | 2024-07-26 13:30:00 | 2024-07-26 14:30:00 | 02:00:00    | 2024/2024-07-28_Belgian_Grand_Prix/2024-07-26_Practice_1/ |
   |  1 |          2024 | Spa-Francorchamps  | Practice 2     | BEL02012       |          1242 |               14 | FORMULA 1 ROLEX BELGIAN GRAND PRIX 2024 | Belgian Grand Prix |                    16 | BEL                    | Belgium                |                     7 | Spa-Francorchamps           |          9568 | Practice 2     | 2024-07-26 17:00:00 | 2024-07-26 18:00:00 | 02:00:00    | 2024/2024-07-28_Belgian_Grand_Prix/2024-07-26_Practice_2/ |
   |  2 |          2024 | Spa-Francorchamps  | Practice 3     | BEL02012       |          1242 |               14 | FORMULA 1 ROLEX BELGIAN GRAND PRIX 2024 | Belgian Grand Prix |                    16 | BEL                    | Belgium                |                     7 | Spa-Francorchamps           |          9569 | Practice 3     | 2024-07-27 12:30:00 | 2024-07-27 13:30:00 | 02:00:00    | 2024/2024-07-28_Belgian_Grand_Prix/2024-07-27_Practice_3/ |
   |  3 |          2024 | Spa-Francorchamps  | Qualifying     | BEL02012       |          1242 |               14 | FORMULA 1 ROLEX BELGIAN GRAND PRIX 2024 | Belgian Grand Prix |                    16 | BEL                    | Belgium                |                     7 | Spa-Francorchamps           |          9570 | Qualifying     | 2024-07-27 16:00:00 | 2024-07-27 17:00:00 | 02:00:00    | 2024/2024-07-28_Belgian_Grand_Prix/2024-07-27_Qualifying/ |
   |  4 |          2024 | Spa-Francorchamps  | Race           | BEL02012       |          1242 |               14 | FORMULA 1 ROLEX BELGIAN GRAND PRIX 2024 | Belgian Grand Prix |                    16 | BEL                    | Belgium                |                     7 | Spa-Francorchamps           |          9574 | Race           | 2024-07-28 15:00:00 | 2024-07-28 17:00:00 | 02:00:00    | 2024/2024-07-28_Belgian_Grand_Prix/2024-07-28_Race/       |


**Get a Meeting by Key.** Alternatively, you can retrieve a meeting using its unique meeting key.

.. code-block:: python

   >>> import livef1 as livef1
   >>> meeting = livef1.get_meeting(season=2024, meeting_key=1242)
   >>> type(meeting)
   <class livef1.models.meeting.Meeting>
   >>> meeting
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

   >>> import livef1
   >>> session = livef1.get_session(season=2024, meeting_identifier="Monza", session_identifier="Race")
   >>> type(session)
   <class livef1.models.meeting.Session>

The :class:`~Session` object acts as the gateway to all available data feeds for the specified session.

Use the `print_topic_names` method to explore the available data feeds for the session. Each feed provides specific information, such as live telemetry, session details, or track conditions:

.. code-block:: python

   >>> session.print_topic_names()
   Session_Info : 
         Details about the current session.
   Archive_Status : 
            Status of archived session data.
   Track_Status : 
            Current conditions and status of the track.
   Session_Data : 
            Raw data for the ongoing session.
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

   >>> data = session.get_data(dataName="Car_Data")
   >>> data
   |    |   SessionKey | timestamp    | Utc                          |   DriverNo | Status   |   X |   Y |   Z |
   |---:|-------------:|:-------------|:-----------------------------|-----------:|:---------|----:|----:|----:|
   |  0 |         9590 | 00:00:30.209 | 2024-09-01T12:08:13.7879709Z |          1 | OnTrack  |   0 |   0 |   0 |
   |  1 |         9590 | 00:00:30.209 | 2024-09-01T12:08:13.7879709Z |          3 | OnTrack  |   0 |   0 |   0 |
   |  2 |         9590 | 00:00:30.209 | 2024-09-01T12:08:13.7879709Z |          4 | OnTrack  |   0 |   0 |   0 |
   |  3 |         9590 | 00:00:30.209 | 2024-09-01T12:08:13.7879709Z |         10 | OnTrack  |   0 |   0 |   0 |
   |  4 |         9590 | 00:00:30.209 | 2024-09-01T12:08:13.7879709Z |         11 | OnTrack  |   0 |   0 |   0 |


.. The `get_data` method returns an object of type :class:`~BasicResult`. This object encapsulates the parsed data in an easily accessible format. To retrieve the underlying data in a structured format, access the value attribute of the :class:`~BasicResult` object:

.. .. code-block:: python
   
..    >>> data.value
..    [
..       {'SessionKey': 9590, 'timestamp': '00: 00: 30.209', 'Utc': '2024-09-01T12: 08: 13.7879709Z', 'DriverNo': '1', 'Status': 'OnTrack', 'X': 0, 'Y': 0, 'Z': 0},
..       {'SessionKey': 9590, 'timestamp': '00: 00: 30.209', 'Utc': '2024-09-01T12: 08: 13.7879709Z', 'DriverNo': '3', 'Status': 'OnTrack', 'X': 0, 'Y': 0, 'Z': 0},
..       {'SessionKey': 9590, 'timestamp': '00: 00: 30.209', 'Utc': '2024-09-01T12: 08: 13.7879709Z', 'DriverNo': '4', 'Status': 'OnTrack', 'X': 0, 'Y': 0, 'Z': 0},
..       {'SessionKey': 9590, 'timestamp': '00: 00: 30.209', 'Utc': '2024-09-01T12: 08: 13.7879709Z', 'DriverNo': '10', 'Status': 'OnTrack', 'X': 0, 'Y': 0, 'Z': 0},
..       {'SessionKey': 9590, 'timestamp': '00: 00: 30.209', 'Utc': '2024-09-01T12: 08: 13.7879709Z', 'DriverNo': '11', 'Status': 'OnTrack', 'X': 0, 'Y': 0, 'Z': 0},
..       .
..       ..
..       ...
..    ]