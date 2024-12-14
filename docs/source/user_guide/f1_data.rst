.. _f1-livetiming-data:
****************************
Formula 1 Live Timing Data
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

1. **Base Information**
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

2. **Yearly Sessions**
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

.. note::
    You can download season data by using LiveF1 ``get_season`` function.

3. **Session Topics**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Endpoint:** :code:`https://livetiming.formula1.com/static/2024/2024-06-23_Spanish_Grand_Prix/2024-06-23_Race/Index.json`

**Description:** Provides available data topics for a specific session.

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

.. note::
    You can download session's data by using LiveF1 ``get_season`` function.

4. **Example: Session Details**
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

.. note::
    You can download session's data by using LiveF1 ``get_data`` function.


.. Downloading Data
.. --------------------------------------------
.. To access the live timing data:

.. - Use an appropriate API client or toolkit such as `LiveF1`.
.. - Subscribe to the desired topics based on your analysis requirements.
.. - Ensure robust handling for real-time streaming or archival for offline analysis.


Data Topics
======================================

Below is a detailed explanation of each data topic, its purpose, and key features.

Session Information - :mod:`SessionInfo`
--------------------------------------

Provides essential details about the current session, including:
- Session type (e.g., practice, qualifying, race).
- Circuit information (name, location, and layout).
- Session duration and progress.

.. list-table::
   :header-rows: 1

   * - Key
     - Type
     - Description
   * - Meeting
     - Object
     - Details about the meeting
   * - Meeting.Key
     - Integer
     - Unique identifier for the meeting
   * - Meeting.Name
     - String
     - Name of the meeting
   * - Meeting.OfficialName
     - String
     - Official name of the meeting
   * - Meeting.Location
     - String
     - Location of the meeting
   * - Meeting.Country
     - Object
     - Details about the country
   * - Meeting.Country.Key
     - Integer
     - Unique identifier for the country
   * - Meeting.Country.Code
     - String
     - ISO code of the country
   * - Meeting.Country.Name
     - String
     - Name of the country
   * - Meeting.Circuit
     - Object
     - Details about the circuit
   * - Meeting.Circuit.Key
     - Integer
     - Unique identifier for the circuit
   * - Meeting.Circuit.ShortName
     - String
     - Short name of the circuit
   * - ArchiveStatus
     - Object
     - Status of the archive
   * - ArchiveStatus.Status
     - String
     - Status of the archive (e.g., "Complete")
   * - Key
     - Integer
     - Unique identifier for the session
   * - Type
     - String
     - Type of the session (e.g., "Race")
   * - Name
     - String
     - Name of the session
   * - StartDate
     - String
     - Start date and time of the session (ISO format)
   * - EndDate
     - String
     - End date and time of the session (ISO format)
   * - GmtOffset
     - String
     - Offset from GMT (e.g., "+02:00")
   * - Path
     - String
     - Path to access the session data


- **Meeting** (Object): Details about the meeting.
    - **Key** (Integer): Unique identifier for the meeting.
    - **Name** (String): Name of the meeting.
    - **OfficialName** (String): Official name of the meeting.
    - **Location** (String): Location of the meeting.
    - **Country** (Object): Details about the country.
        - **Key** (Integer): Unique identifier for the country.
        - **Code** (String): ISO code of the country.
        - **Name** (String): Name of the country.
    - **Circuit** (Object): Details about the circuit.
        - **Key** (Integer): Unique identifier for the circuit.
        - **ShortName** (String): Short name of the circuit.
- **ArchiveStatus** (Object): Status of the archive.
    - **Status** (String): Status of the archive (e.g., "Complete").
- **Key** (Integer): Unique identifier for the session.
- **Type** (String): Type of the session (e.g., "Race").
- **Name** (String): Name of the session.
- **StartDate** (String): Start date and time of the session (ISO format).
- **EndDate** (String): End date and time of the session (ISO format).
- **GmtOffset** (String): Offset from GMT (e.g., "+02:00").
- **Path** (String): Path to access the session data.


Archive Status
--------------------------------------
**Topic:** ArchiveStatus

Tracks the status of archived session data, indicating:
- Availability of historical data for analysis.
- Updates on archived datasets.

Track Status
--------------------------------------
**Topic:** TrackStatus

Describes current track conditions and statuses:
- Weather and temperature conditions.
- Flags indicating incidents (yellow, red, or green).
- Wetness levels and safety car presence.

Session Data
--------------------------------------
**Topic:** SessionData

Provides raw data for the session, including:
- Lap and sector times.
- Driver and car performance metrics.
- Key session milestones.

Content Streams
--------------------------------------
**Topic:** ContentStreams

Streams multimedia content related to the session:
- Video highlights.
- Image captures of key moments.

Audio Streams
--------------------------------------
**Topic:** AudioStreams

Delivers live audio commentary and team radio communications:
- Race commentary feeds.
- Select driver-to-team audio snippets.

Extrapolated Clock
--------------------------------------
**Topic:** ExtrapolatedClock

Predicts session time data:
- Remaining session time or laps.
- Calculations based on historical and current pace.

Tyre Stint Series
--------------------------------------
**Topic:** TyreStintSeries

Analyzes tyre usage over stints:
- Compound usage and wear rates.
- Strategy evaluation for tyre selection.

Session Status
--------------------------------------
**Topic:** SessionStatus

Displays the live session status:
- Current flag status (green, yellow, red).
- Notifications for major events.

Timing Data (F1 Specific)
--------------------------------------
**Topic:** TimingDataF1

Specialized timing information for Formula 1:
- Sector times.
- Driver deltas and gaps.

Timing Data (General)
--------------------------------------
**Topic:** TimingData

Generic timing data for the session:
- All racing categories.
- Laps and intervals.

Driver List
--------------------------------------
**Topic:** DriverList

Provides a list of active drivers:
- Car numbers and team names.
- Driver names and abbreviations.

Lap Series
--------------------------------------
**Topic:** LapSeries

Tracks laps completed:
- Lap times for each driver.
- Fastest lap indicators.

Top Three
--------------------------------------
**Topic:** TopThree

Highlights the top three drivers:
- Current positions.
- Time differences.

Timing Application Data
--------------------------------------
**Topic:** TimingAppData

Provides timing data from the Formula 1 application:
- Aggregated sector data.
- Driver gaps and intervals.

Timing Statistics
--------------------------------------
**Topic:** TimingStats

Analyzes timing data statistically:
- Averages, medians, and trends.
- Comparisons across sessions.

Heartbeat
--------------------------------------
**Topic:** Heartbeat

Regularly sends a system status signal:
- Ensures stream connectivity.
- Monitors data stream health.

Weather Data
--------------------------------------
**Topic:** WeatherData

Displays current weather conditions:
- Temperature, humidity, and wind.
- Rain predictions.

Weather Data Series
--------------------------------------
**Topic:** WeatherDataSeries

Offers historical weather data:
- Temperature trends.
- Rainfall patterns.

Position Data (Z Coordinate)
--------------------------------------
**Topic:** Position.z

Tracks vertical position data:
- Insights into elevation changes.
- Vertical motion analysis.

Car Data (Z Coordinate)
--------------------------------------
**Topic:** CarData.z

Analyzes car data along the Z axis:
- Suspension and vertical acceleration.

Team Audio and Race Control Messages
--------------------------------------
**Topic:** TlaRcm

Provides team audio and race control messages:
- Strategic communications.
- Official instructions and penalties.

Race Control Messages
--------------------------------------
**Topic:** RaceControlMessages

Broadcasts race control instructions:
- Penalties, warnings, and notes.
- Decisions affecting race outcomes.

Pit Lane Time Collection
--------------------------------------
**Topic:** PitLaneTimeCollection

Records pit lane timing data:
- Entry and exit times.
- Time spent in the pit lane.

Current Tyres
--------------------------------------
**Topic:** CurrentTyres

Details tyres currently in use:
- Compound type and condition.
- Wear levels and performance.

Driver Race Information
--------------------------------------
**Topic:** DriverRaceInfo

Provides individual driver performance metrics:
- Acceleration, speed, and fuel data.
- Driver-specific telemetry.

Team Radio
--------------------------------------
**Topic:** TeamRadio

Streams team radio communications:
- Real-time strategic discussions.
- Issue reporting and updates.

Championship Predictions
--------------------------------------
**Topic:** ChampionshipPrediction

Predicts championship outcomes:
- Based on current performance and standings.
- Statistical modeling and machine learning predictions.

Overtake Series
--------------------------------------
**Topic:** OvertakeSeries

Tracks overtakes during the session:
- Aggressive and defensive maneuvers.
- Key moments impacting race positions.

Driver Score
--------------------------------------
**Topic:** DriverScore

Calculates driver performance scores:
- Based on statistical and telemetry analysis.

Special Feed
--------------------------------------
**Topic:** SPFeed

Delivers a special data feed:
- Auxiliary metrics and session-specific insights.

Pit Stop Series
--------------------------------------
**Topic:** PitStopSeries

Tracks multiple pit stops:
- Strategy changes.
- Total pit stop durations.

Pit Stop
--------------------------------------
**Topic:** PitStop

Details individual pit stops:
- Entry and exit analysis.
- Errors and delays.

Lap Count
--------------------------------------
**Topic:** LapCount

Monitors laps completed:
- Total laps.
- Progress metrics.

Enhancing the Page
------------------
To enhance this documentation page further, consider adding:

1. **Visual Examples:** Include charts or images for topics like `TrackStatus` or `WeatherData`.
2. **Code Snippets:** Show examples of how to query and process data for each topic.
3. **Tutorials:** Add guides on setting up streams and interpreting the data.
4. **Glossary:** Define technical terms (e.g., stint, compound, deltas).
5. **FAQs:** Address common questions about data accuracy and integration.

By integrating these features, the page will become more accessible and informative for a diverse audience.

