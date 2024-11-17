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

   import livef1 as livef1

Get season object and its meetings + sessions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To fetch season data for 2024:

.. code-block:: python

   season = livef1.get_season(
       season=2024
   )

   print(season)  # Shows the dataframe table of sessions and their information
   print(season.meetings)  # Get meeting objects

Sample output (as pandas DataFrame):

.. code-block::

   | MeetingID | MeetingName | Location | Date       | SessionCount |
   |-----------|-------------|----------|------------|--------------|
   | 1001      | Italian GP  | Monza    | 2024-09-01 | 5            |
   | 1002      | French GP   | Le Castellet | 2024-07-10 | 5        |
   | 1003      | British GP  | Silverstone | 2024-06-29 | 5         |

Get meeting object and its sessions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To fetch meeting data for the Italian Grand Prix:

.. code-block:: python

   meeting = livef1.get_meeting(
       season=2024,
       location="Monza"
   )

   print(meeting)  # Shows the dataframe table of sessions and their information
   print(meeting.sessions)  # Get session objects

Sample output (as pandas DataFrame):

.. code-block::

   | SessionID | SessionType | StartTime           | EndTime             |
   |-----------|-------------|---------------------|---------------------|
   | 3001      | Practice 1  | 2024-09-01 10:00:00 | 2024-09-01 11:30:00 |
   | 3002      | Qualifying  | 2024-09-01 14:00:00 | 2024-09-01 15:00:00 |
   | 3003      | Race        | 2024-09-02 14:00:00 | 2024-09-02 16:00:00 |

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