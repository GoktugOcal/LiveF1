Getting Started
===========

Welcome to LiveF1! This guide will walk you through the installation process and help you get up and running with the toolkit.

Installation
------------

Install via pip
^^^^^^^^^^^^^^^

The easiest way to install LiveF1 is through pip. Run the following command in your terminal:

.. code-block:: bash

   pip install livef1

Install from source
^^^^^^^^^^^^^^^^^^^^

If you want to install the latest development version or contribute to LiveF1, follow these steps:

1. Clone the repository:

   .. code-block:: bash

      git clone https://github.com/yourusername/LiveF1.git

2. Navigate into the project directory:

   .. code-block:: bash

      cd LiveF1

3. Install dependencies and the package:

   .. code-block:: bash

      pip install -r requirements.txt
      pip install .

Quick Start
-----------

Once LiveF1 is installed, you can start using it to fetch real-time or historical F1 data.

Import the library
^^^^^^^^^^^^^^^^^^

Start by importing LiveF1:

.. code-block:: python

   >>> import livef1 as livef1

Get a season object with its meetings and sessions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The get_season function in the livef1 package is used to retrieve detailed information about a Formula 1 season. This includes an overview of the meetings (Grand Prix events) and their respective sessions.

.. code-block:: python

   >>> import livef1 as livef1
   >>> season = livef1.get_season(season=2021)
   >>> type(season)
   <class 'livef1.models.season.Season'>
   >>> season
   |    |   Meeting Key | Meeting Code   | Meeting Name              | Meeting Circuit Shortname     |   No. Sessions | Race Startdate      |
   |---:|--------------:|:---------------|:--------------------------|:------------------------------|---------------:|:--------------------|
   |  0 |          1064 | BRN0104        | Bahrain Grand Prix        | Sakhir                        |              5 | 2021-03-28 18:00:00 |
   |  1 |          1065 | ITA0110        | Emilia Romagna Grand Prix | Imola                         |              5 | 2021-04-18 15:00:00 |
   |  2 |          1066 | POR0401        | Portuguese Grand Prix     | Algarve International Circuit |              5 | 2021-05-02 15:00:00 |
   |  3 |          1086 | ESP0111        | Spanish Grand Prix        | Catalunya                     |              5 | 2021-05-09 15:00:00 |
   |  4 |          1067 | MON0112        | Monaco Grand Prix         | Monte Carlo                   |              5 | 2021-05-23 15:00:00 |

The `season` object is an instance of the `Season` class, providing access to structured season data, including meetings and their corresponding sessions.

Once you retrieve a season, you can inspect its contents by printing the object. The output provides an overview of the meetings within the season, formatted as a table. Each row corresponds to a Grand Prix event, and the columns provide key details.

Get a meeting object and its sessions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To load session data, such as telemetry or other statistics:

.. code-block:: python

   session = livef1.get_session(
       season=2024,
       location="Monza",
       session="Race"
   )

   session.get_topic_names()  # load /Info.json
   print(session.topic_names_info)

Sample JSON output:

.. code-block::

   {
     "SessionInfo": {
       "KeyFramePath": "SessionInfo.json",
       "StreamPath": "SessionInfo.jsonStream"
     },
     "ArchiveStatus": {
       "KeyFramePath": "ArchiveStatus.json",
       "StreamPath": "ArchiveStatus.jsonStream"
     },
     "Position.z": {
       "KeyFramePath": "Position.z.json",
       "StreamPath": "Position.z.jsonStream"
     },
     ...
   }

Load specific data by name of data
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To load specific data, use the following code:

.. code-block:: python

   data = session.get_data(
       dataName="Position.z",
       dataType="StreamPath",
       stream=True
   )

   print(type(data))
   # <class 'livef1.data_processing.data_models.BasicResult'>

   print(data)
   #     SessionKey     timestamp                           Utc DriverNo   Status     X      Y     Z
   # 0         9590  00:00:30.209  2024-09-01T12:08:13.7879709Z        1  OnTrack     0      0     0
   # 1         9590  00:00:30.209  2024-09-01T12:08:13.7879709Z        3  OnTrack     0      0     0
   # 2         9590  00:00:30.209  2024-09-01T12:08:13.7879709Z        4  OnTrack     0      0     0
   # 3         9590  00:00:30.209  2024-09-01T12:08:13.7879709Z       10  OnTrack     0      0     0

   print(data.value)
   # [
   #   {'SessionKey': 9590, 'timestamp': '00:00:30.209', 'Utc': '2024-09-01T12:08:13.7879709Z', 'DriverNo': '1', 'Status': 'OnTrack', 'X': 0, 'Y': 0, 'Z': 0},
   #   {'SessionKey': 9590, 'timestamp': '00:00:30.209', 'Utc': '2024-09-01T12:08:13.7879709Z', 'DriverNo': '3', 'Status': 'OnTrack', 'X': 0, 'Y': 0, 'Z': 0},
   #   {'SessionKey': 9590, 'timestamp': '00:00:30.209', 'Utc': '2024-09-01T12:08:13.7879709Z', 'DriverNo': '4', 'Status': 'OnTrack', 'X': 0, 'Y': 0, 'Z': 0},
   #   ...
   # ]

Troubleshooting
---------------

If you run into issues during installation, here are a few common troubleshooting steps:

- Ensure you have Python 3.6+ and pip installed.
- If you get a `ModuleNotFoundError`, try reinstalling the package using `pip install --upgrade livef1`.
- Check for issues in your internet connection if you’re using the real-time data features.

Next Steps
----------

- After completing the installation and testing, head over to the :doc:`../user_guide/index` for detailed tutorials on how to work with the data.
- If you’re ready to explore the API in detail, check the :doc:`../api_reference/index`.

Happy Racing!
-------------