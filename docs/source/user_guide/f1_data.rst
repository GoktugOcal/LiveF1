.. _f1-livetiming-data:
****************************
Formula 1 LiveTiming Data
****************************

Formula 1 live timing data provides comprehensive insights into the performance of drivers, teams, and cars during races. This data is critical for real-time analytics, historical analysis, and developing strategies for races.

Source of Data
======================================
Formula 1 live timing data delivers real-time and historical telemetry, timing, and contextual data. This data is critical for real-time analytics, historical analysis, and developing strategies for races.

API Structure
--------------------------------------------

.. Document Subsubsection
.. ^^^^^^^^^^^^^^^^^^^^^^

.. Document Paragraph
.. """"""""""""""""""

The live timing API follows a structured format to ensure efficient data access. Each API address corresponds to a specific endpoint, which streams or delivers data for various aspects of Formula 1 sessions. These endpoints can be accessed via HTTP requests.

**Key Points:**

- Base URL: :code:`https://livetiming.formula1.com/`
- Endpoints: Each topic is mapped to an endpoint path.
- Response Format: Data is returned in JSON format.

**Accessing the Data:**

1. Use the base URL to connect to the API.
2. Append specific paths for desired data.
3. Process the JSON responses for your use case.

API Addresses and Endpoints
--------------------------------------------

Here is a list of key API addresses and their respective endpoints:

1. Base Information
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Endpoint:** :code:`https://livetiming.formula1.com/static/Index.json`

**Description:** Provides a list of available years and their corresponding paths.

**Response Example:**

.. code-block:: json

    {
        "Years": [
            {
                "Year": 2024,
                "Path": "2024/"
            }
        ]
    }

.. list-table::
    :header-rows: 1

    * - Key
    - Type
    - Description
    * - Years
    - Array
    - List of available years and paths
    * - Year
    - Integer
    - The year of the data
    * - Path
    - String
    - Path to access the year-specific data

2. Yearly Sessions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Endpoint:** :code:`https://livetiming.formula1.com/static/2024/Index.json`

**Description:** Lists races and sessions for the year 2024.

**Response Example:**

.. code-block:: json

    {
        "Year": 2024,
        "Meetings": [
            {
                "Key": 1238,
                "Name": "Spanish Grand Prix",
                "Sessions": [
                    {
                        "Key": 9539,
                        "Type": "Race",
                        "Path": "2024/2024-06-23_Spanish_Grand_Prix/2024-06-23_Race/"
                    },
                    // ...other sessions
                ]
            },
            // ...other meetings
        ]
    }

.. list-table::
    :header-rows: 1

    * - Key
      - Type
      - Description
    * - Year
      - Integer
      - The year of the data
    * - Meetings
      - Array
      - List of races and associated sessions
    * - Key
      - Integer
      - Unique identifier for the meeting
    * - Name
      - String
      - Name of the meeting
    * - Sessions
      - Array
      - List of sessions for the meeting

.. seealso::
    You can download season data by using LiveF1 ``get_season`` function.

3. Session Topics
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Endpoint:** :code:`https://livetiming.formula1.com/static/2024/2024-06-23_Spanish_Grand_Prix/2024-06-23_Race/Index.json`

**Description:** Provides available data topics for a specific session.

.. note::
   The data feeds is further explained in :ref:`data_topics` section.

**Response Example:**

.. code-block:: json

    {
        "Feeds": {
            "SessionInfo": {
                "KeyFramePath": "SessionInfo.json",
                "StreamPath": "SessionInfo.jsonStream"
            },
            "TrackStatus": {
                "KeyFramePath": "TrackStatus.json",
                "StreamPath": "TrackStatus.jsonStream"
            },
            // ...other data topics
        }
    }

.. list-table::
    :header-rows: 1

    * - Key
      - Type
      - Description
    * - Feeds
      - Object
      - Contains different data feed categories
    * - SessionInfo
      - Object
      - Details about the session
    * - KeyFramePath
      - String
      - Path to the keyframe data
    * - StreamPath
      - String
      - Path to the data stream
    * - TrackStatus
      - Object
      - Details about the track status

.. seealso::
    You can download session's data by using LiveF1 ``get_season`` function.

4. Example: Session Details
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Endpoint:** :code:`https://livetiming.formula1.com/static/2024/2024-06-23_Spanish_Grand_Prix/2024-06-23_Race/SessionInfo.json`

**Description:** Contains detailed information about the session.

**Response Example:**

.. code-block:: json

    {
        "Meeting": {
            "Name": "Spanish Grand Prix",
            "Location": "Barcelona",
            "Country": {
                "Code": "ESP",
                "Name": "Spain"
            }
        },
        "Key": 9539,
        "Type": "Race",
        "Name": "Race",
        "StartDate": "2024-06-23T15:00:00",
        "EndDate": "2024-06-23T17:00:00"
    }

.. seealso::
    You can download session's data by using LiveF1 ``get_data`` function.


.. Downloading Data
.. --------------------------------------------
.. To access the live timing data:

.. - Use an appropriate API client or toolkit such as `LiveF1`.
.. - Subscribe to the desired topics based on your analysis requirements.
.. - Ensure robust handling for real-time streaming or archival for offline analysis.