.. _data_topics:
**********************************
LiveTiming Data Topics
**********************************

Below is a detailed explanation of each data topic, its purpose, and key features.

.. admonition:: HTTP Request
   :class: important

   GET https://livetiming.formula1.com/static/{year}/{meeting_path}/{session_path}/{topic}

.. list-table::
    :header-rows: 1

    * - Key
      - Path
      - Description
    * - `Session Information <#session-information-sessioninfo>`_
      - :code:`SessionInfo`
      - Provides details about the session, such as session type, start and end times, and other key session attributes.
    * - `Archive Status <#archive-status-archivestatus>`_
      - :code:`ArchiveStatus`
      - Describes the status of archived data, including whether data is available for past sessions.
    * - `Track Status <#track-status-trackstatus>`_
      - :code:`TrackStatus`
      - Provides the current state of the track, including whether the track is dry, wet, or under specific conditions.
    * - `Session Data <#session-data-sessiondata>`_
      - :code:`SessionData`
      - Includes detailed data from a session such as lap times, intervals, and driver performance metrics.
    * - `Content Streams <#content-streams-contentstreams>`_
      - :code:`ContentStreams`
      - Refers to streams of content, such as live timing, telemetry, and other media available during a race.
    * - `Audio Streams <#audio-streams-audiostreams>`_
      - :code:`AudioStreams`
      - Represents the real-time audio streams available, such as team radio and commentary during a race.
    * - `Extrapolated Clock <#extrapolated-clock-extrapolatedclock>`_
      - :code:`ExtrapolatedClock`
      - Provides extrapolated timing data for situations where real-time clocks may not be available.
    * - `Tyre Stint Series <#tyre-stint-series-tyrestintseries>`_
      - :code:`TyreStintSeries`
      - Contains data related to the usage of tyres throughout a race, including stint duration and tire performance.
    * - `Session Status <#session-status-sessionstatus>`_
      - :code:`SessionStatus`
      - Shows the current status of the session, such as whether it's under a red flag, green flag, or has been delayed.
    * - `Timing Data F1 <#timing-data-f1-timingdataf1>`_
      - :code:`TimingDataF1`
      - Includes specific timing data for Formula 1 races, including lap times, sector times, and pit stop information.
    * - `Timing Data <#timing-data-timingdata>`_
      - :code:`TimingData`
      - General timing data, not necessarily tied to F1, covering the details like laps, sector times, and overall race performance.
    * - `Driver List <#driver-list-driverlist>`_
      - :code:`DriverList`
      - Provides a list of all drivers participating in a session, along with key driver information.
    * - `Lap Series <#lap-series-lapseries>`_
      - :code:`LapSeries`
      - A collection of lap data over the course of a session, including laps completed, times, and performance metrics.
    * - `Top Three <#top-three-topthree>`_
      - :code:`TopThree`
      - Data highlighting the top three drivers in terms of performance, timing, or race position.
    * - `Timing Application Data <#timing-application-data-timingappdata>`_
      - :code:`TimingAppData`
      - Data related to the application managing the timing information during a race or session.
    * - `Timing Statistics <#timing-statistics-timingstats>`_
      - :code:`TimingStats`
      - Statistical data derived from timing information, such as average lap times, fastest laps, and consistency.
    * - `Heartbeat <#heartbeat-heartbeat>`_
      - :code:`Heartbeat`
      - A signal indicating the system is active and operational, often used to monitor data flow during a race.
    * - `Weather Data <#weather-data-weatherdata>`_
      - :code:`WeatherData`
      - Weather-related data for the track, including temperature, wind speed, humidity, and other meteorological conditions.
    * - `Weather Data Series <#weather-data-series-weatherdataseries>`_
      - :code:`WeatherDataSeries`
      - A series of weather data over time, providing insights into how weather conditions change during a race or session.
    * - `Position Data <#position-data-position.z>`_
      - :code:`Position.z`
      - Data about the positions of cars on the track, including real-time location and distance to the leader.
    * - `Car Data <#car-data-cardata.z>`_
      - :code:`CarData.z`
      - Information related to the cars, such as speed, tire wear, fuel levels, and engine data.
    * - `Team Audio and Race Control Messages <#team-audio-and-race-control-messages-tlarcm>`_
      - :code:`TlaRcm`
      - Audio and race control messages related to team communication and instructions during the race.
    * - `Race Control Messages <#race-control-messages-racecontrolmessages>`_
      - :code:`RaceControlMessages`
      - Official messages and updates from race control, often related to race flags, penalties, or instructions.
    * - `Pit Lane Time Collection <#pit-lane-time-collection-pitlanetimecollection>`_
      - :code:`PitLaneTimeCollection`
      - Data regarding the times spent in the pit lane, including pit stop duration and strategy insights.
    * - `Current Tyres <#current-tyres-currenttyres>`_
      - :code:`CurrentTyres`
      - Information on the tyres currently in use by each car, including type and performance metrics.
    * - `Driver Race Information <#driver-race-information-driverraceinfo>`_
      - :code:`DriverRaceInfo`
      - Specific information regarding each driver's performance in a race, such as position, time gaps, and lap data.
    * - `Team Radio <#team-radio-teamradio>`_
      - :code:`TeamRadio`
      - Communication between the driver and the team, typically audio, for race updates, strategies, and instructions.
    * - `Championship Predictions <#championship-predictions-championshipprediction>`_
      - :code:`ChampionshipPrediction`
      - Predictive data regarding the potential outcome of the championship based on race results and standings.
    * - `Overtake Series <#overtake-series-overtakeseries>`_
      - :code:`OvertakeSeries`
      - Data regarding overtakes during a race, including the number, timing, and type of overtakes made.
    * - `Driver Score <#driver-score-driverscore>`_
      - :code:`DriverScore`
      - A scoring system used to evaluate driver performance throughout a session or race, including metrics like speed, consistency, and penalties.
    * - `Special Feed <#special-feed-spfeed>`_
      - :code:`SPFeed`
      - Special feeds for specific data points, often related to unique events or custom requests during a race.
    * - `Pit Stop Series <#pit-stop-series-pitstopseries>`_
      - :code:`PitStopSeries`
      - A series of pit stops taken by drivers, including times, strategies, and analysis.
    * - `Pit Stop <#pit-stop-pitstop>`_
      - :code:`PitStop`
      - Data about a specific pit stop, including entry and exit times, tire changes, and fuel information.
    * - `Lap Count <#lap-count-lapcount>`_
      - :code:`LapCount`
      - The total number of laps completed in a race or session, including total laps driven and laps remaining.


Session Information - :mod:`SessionInfo`
--------------------------------------

Provides essential details about the current session, including:
- Session type (e.g., practice, qualifying, race).
- Circuit information (name, location, and layout).
- Session duration and progress.


.. admonition:: Sample Request
    :class: warning

        https://livetiming.formula1.com/static/2024/2024-07-28_Belgian_Grand_Prix/2024-07-28_Race/SessionInfo.json

    .. tabs::

        .. code-tab:: shell

            curl "https://livetiming.formula1.com/static/2024/2024-07-28_Belgian_Grand_Prix/2024-07-28_Race/SessionInfo.json"

        .. code-tab:: python

            from urllib.request import urlopen
            import json

            url = "https://livetiming.formula1.com/static/2024/2024-07-28_Belgian_Grand_Prix/2024-07-28_Race/SessionInfo.json"
            response = urlopen(url)
            data = json.loads(response.read().decode('utf-8'))
            print(data)
        
        .. code-tab:: javascript

            fetch('https://livetiming.formula1.com/static/2024/2024-07-28_Belgian_Grand_Prix/2024-07-28_Race/SessionInfo.json')
                .then(response => response.json())
                .then(jsonContent => console.log(jsonContent));

.. admonition:: Response
    :class: info

    .. code-block:: json

        {
            "Meeting": {
                "Key": 1242,
                "Name": "Belgian Grand Prix",
                "OfficialName": "FORMULA 1 ROLEX BELGIAN GRAND PRIX 2024",
                "Location": "Spa-Francorchamps",
                "Country": {
                    "Key": 16,
                    "Code": "BEL",
                    "Name": "Belgium"
                },
                "Circuit": {
                    "Key": 7,
                    "ShortName": "Spa-Francorchamps"
                }
            },
            "ArchiveStatus": {
                "Status": "Complete"
            },
            "Key": 9574,
            "Type": "Race",
            "Name": "Race",
            "StartDate": "2024-07-28T15:00:00",
            "EndDate": "2024-07-28T17:00:00",
            "GmtOffset": "02:00:00",
            "Path": "2024/2024-07-28_Belgian_Grand_Prix/2024-07-28_Race/"
        }

**Attributes:**

.. list-table::
   :header-rows: 1

   * - Key
     - Path
     - Description
   * - Meeting
     - ``Meeting``
     - Details about the meeting
   * - Key
     - ``Meeting.Key``
     - Unique identifier for the meeting
   * - Name
     - ``Meeting.Name``
     - Name of the meeting
   * - OfficialName
     - ``Meeting.OfficialName``
     - Official name of the meeting
   * - Location
     - ``Meeting.Location``
     - Location of the meeting
   * - Country
     - ``Meeting.Country``
     - Details about the country
   * - Key
     - ``Meeting.Country.Key``
     - Unique identifier for the country
   * - Code
     - ``Meeting.Country.Code``
     - ISO code of the country
   * - Name
     - ``Meeting.Country.Name``
     - Name of the country
   * - Circuit
     - ``Meeting.Circuit``
     - Details about the circuit
   * - Key
     - ``Meeting.Circuit.Key``
     - Unique identifier for the circuit
   * - ShortName
     - ``Meeting.Circuit.ShortName``
     - Short name of the circuit
   * - ArchiveStatus
     - ``ArchiveStatus``
     - Status of the archive
   * - Status
     - ``ArchiveStatus.Status``
     - Status of the archive (e.g., "Complete")
   * - Key
     - ``Key``
     - Unique identifier for the session
   * - Type
     - ``Type``
     - Type of the session (e.g., "Race")
   * - Name
     - ``Name``
     - Name of the session
   * - StartDate
     - ``StartDate``
     - Start date and time of the session (ISO format)
   * - EndDate
     - ``EndDate``
     - End date and time of the session (ISO format)
   * - GmtOffset
     - ``GmtOffset``
     - Offset from GMT (e.g., "+02:00")
   * - Path
     - ``Path``
     - Path to access the session data



Archive Status - :mod:`ArchiveStatus`
--------------------------------------

Tracks the status of archived session data, indicating:
- Availability of historical data for analysis.
- Updates on archived datasets.

.. admonition:: Sample Request
    :class: warning

        https://livetiming.formula1.com/static/2024/2024-07-28_Belgian_Grand_Prix/2024-07-28_Race/ArchiveStatus.json

    .. tabs::

        .. code-tab:: shell

            curl "https://livetiming.formula1.com/static/2024/2024-07-28_Belgian_Grand_Prix/2024-07-28_Race/ArchiveStatus.json"

        .. code-tab:: python

            from urllib.request import urlopen
            import json

            url = "https://livetiming.formula1.com/static/2024/2024-07-28_Belgian_Grand_Prix/2024-07-28_Race/ArchiveStatus.json"
            response = urlopen(url)
            data = json.loads(response.read().decode('utf-8'))
            print(data)
        
        .. code-tab:: javascript

            fetch('https://livetiming.formula1.com/static/2024/2024-07-28_Belgian_Grand_Prix/2024-07-28_Race/ArchiveStatus.json')
                .then(response => response.json())
                .then(jsonContent => console.log(jsonContent));

.. admonition:: Response
    :class: info

    .. code-block:: json

        {
            "Status": "Complete"
        }

**Attributes:**

.. list-table::
   :header-rows: 1

   * - Key
     - Path
     - Description
   * - Status
     - ``Status``
     - Status of the archive (e.g., "Complete")

Track Status - :mod:`TrackStatus`
--------------------------------------

Describes current track conditions and statuses:
- Weather and temperature conditions.
- Flags indicating incidents (yellow, red, or green).
- Wetness levels and safety car presence.

.. admonition:: Sample Request
    :class: warning

        https://livetiming.formula1.com/static/2024/2024-07-28_Belgian_Grand_Prix/2024-07-28_Race/TrackStatus.jsonStream

    .. tabs::

        .. code-tab:: shell

            curl "https://livetiming.formula1.com/static/2024/2024-07-28_Belgian_Grand_Prix/2024-07-28_Race/TrackStatus.jsonStream"

        .. code-tab:: python

            from urllib.request import urlopen
            import json

            url = "https://livetiming.formula1.com/static/2024/2024-07-28_Belgian_Grand_Prix/2024-07-28_Race/TrackStatus.jsonStream"
            response = urlopen(url)
            data = json.loads(response.read().decode('utf-8'))
            print(data)
        
        .. code-tab:: javascript

            fetch('https://livetiming.formula1.com/static/2024/2024-07-28_Belgian_Grand_Prix/2024-07-28_Race/TrackStatus.jsonStream')
                .then(response => response.json())
                .then(jsonContent => console.log(jsonContent));

.. admonition:: Response
    :class: info

    .. code-block:: json

        {
            "Status": "1",
            "Message": "AllClear"
        }

**Attributes:**

.. list-table::
   :header-rows: 1

   * - Key
     - Path
     - Description
   * - Status
     - ``Status``
     - Status of the track (e.g., "1")
   * - Message
     - ``Message``
     - Message regarding the track status (e.g., "AllClear")

Session Data - :mod:`SessionData`
--------------------------------------

Provides raw data for the session, including:
- Lap and sector times.
- Driver and car performance metrics.
- Key session milestones.

.. admonition:: Sample Request
    :class: warning

        https://livetiming.formula1.com/static/2024/2024-07-28_Belgian_Grand_Prix/2024-07-28_Race/SessionData.json

    .. tabs::

        .. code-tab:: shell

            curl "https://livetiming.formula1.com/static/2024/2024-07-28_Belgian_Grand_Prix/2024-07-28_Race/SessionData.json"

        .. code-tab:: python

            import requests

            url = "https://livetiming.formula1.com/static/2024/2024-07-28_Belgian_Grand_Prix/2024-07-28_Race/SessionData.json"
            response = requests.get(url)
            data = response.json()
            print(data)

        .. code-tab:: javascript

            fetch('https://livetiming.formula1.com/static/2024/2024-07-28_Belgian_Grand_Prix/2024-07-28_Race/SessionData.json')
                .then(response => response.json())
                .then(jsonContent => console.log(jsonContent));

.. admonition:: Response
    :class: info

    .. code-block:: json

        {
            "Series": [
                {"Utc": "2024-07-28T12:09:48.568Z", "Lap": 1},
                {"Utc": "2024-07-28T13:20:21.984Z", "Lap": 10},
                {"Utc": "2024-07-28T14:20:15.676Z", "Lap": 43},
                {"Utc": "2024-07-28T14:22:02.956Z", "Lap": 44}
            ],
            "StatusSeries": [
                {"Utc": "2024-07-28T12:05:34.051Z", "TrackStatus": "Yellow"},
                {"Utc": "2024-07-28T13:03:52.741Z", "SessionStatus": "Started"},
                {"Utc": "2024-07-28T14:23:50.019Z", "SessionStatus": "Finished"}
            ]
        }

**Attributes:**

.. list-table::
   :header-rows: 1

   * - Key
     - Path
     - Description
   * - Series
     - ``Series``
     - Data about lap timings
   * - Utc
     - ``Series.Utc``
     - UTC timestamp of the event
   * - Lap
     - ``Series.Lap``
     - Lap number of the session
   * - StatusSeries
     - ``StatusSeries``
     - Data about session status changes
   * - Utc
     - ``StatusSeries.Utc``
     - UTC timestamp of the status update
   * - TrackStatus
     - ``StatusSeries.TrackStatus``
     - Track status at the given time (e.g., "Yellow", "AllClear")
   * - SessionStatus
     - ``StatusSeries.SessionStatus``
     - Session status at the given time (e.g., "Started", "Finished")

Content Streams - :mod:`ContentStreams`
--------------------------------------

Streams multimedia content related to the session:
- Video highlights.
- Image captures of key moments.

.. admonition:: Sample Request
    :class: warning

        https://livetiming.formula1.com/static/2024/2024-07-28_Belgian_Grand_Prix/2024-07-28_Race/ContentStreams.json

    .. tabs::

        .. code-tab:: shell

            curl "https://livetiming.formula1.com/static/2024/2024-07-28_Belgian_Grand_Prix/2024-07-28_Race/ContentStreams.json"

        .. code-tab:: python

            import requests

            url = "https://livetiming.formula1.com/static/2024/2024-07-28_Belgian_Grand_Prix/2024-07-28_Race/ContentStreams.json"
            response = requests.get(url)
            data = response.json()
            print(data)

        .. code-tab:: javascript

            fetch('https://livetiming.formula1.com/static/2024/2024-07-28_Belgian_Grand_Prix/2024-07-28_Race/ContentStreams.json')
                .then(response => response.json())
                .then(jsonContent => console.log(jsonContent));

.. admonition:: Response
    :class: info

    .. code-block:: json

        {
            "Streams": [
                {
                    "Type": "Commentary",
                    "Name": "monterosa",
                    "Language": "en",
                    "Uri": "https://interactioncloud.formula1.com/?h=cdn.monterosa.cloud&p=222568ff-a8d4-4e3a-b9e2-63e185e2d964&e=dfb3526d-bed7-4f4b-b7d6-014a1268882a"
                },
                {
                    "Type": "Audio",
                    "Name": "Live coverage (EN)",
                    "Language": "en",
                    "Uri": "https://dtksvu0irgynk.cloudfront.net/out/v1/7ed89990eb2a4d39870ff19793519937/index.m3u8"
                }
            ]
        }

**Attributes:**

.. list-table::
   :header-rows: 1

   * - Key
     - Path
     - Description
   * - Streams
     - ``Streams``
     - A list of available content streams
   * - Type
     - ``Streams.Type``
     - Type of the stream (e.g., "Commentary", "Audio")
   * - Name
     - ``Streams.Name``
     - Stream name or identifier
   * - Language
     - ``Streams.Language``
     - Language of the stream
   * - Uri
     - ``Streams.Uri``
     - URL to access the stream
   * - Utc
     - ``Streams.Utc``
     - UTC timestamp for the stream

Audio Streams - :mod:`AudioStreams`
--------------------------------------

Delivers live audio commentary and team radio communications:
- Race commentary feeds.
- Select driver-to-team audio snippets.

.. admonition:: Sample Request
    :class: warning

        https://livetiming.formula1.com/static/2024/2024-07-28_Belgian_Grand_Prix/2024-07-28_Race/AudioStreams.json

    .. tabs::

        .. code-tab:: shell

            curl "https://livetiming.formula1.com/static/2024/2024-07-28_Belgian_Grand_Prix/2024-07-28_Race/AudioStreams.json"

        .. code-tab:: python

            import requests

            url = "https://livetiming.formula1.com/static/2024/2024-07-28_Belgian_Grand_Prix/2024-07-28_Race/AudioStreams.json"
            response = requests.get(url)
            data = response.json()
            print(data)

        .. code-tab:: javascript

            fetch('https://livetiming.formula1.com/static/2024/2024-07-28_Belgian_Grand_Prix/2024-07-28_Race/AudioStreams.json')
                .then(response => response.json())
                .then(jsonContent => console.log(jsonContent));

.. admonition:: Response
    :class: info

    .. code-block:: json

        {
            "Streams": [
                {
                    "Name": "Live coverage (EN)",
                    "Language": "en",
                    "Uri": "https://dtksvu0irgynk.cloudfront.net/out/v1/7ed89990eb2a4d39870ff19793519937/index.m3u8",
                    "Path": "Live_coverage_(EN)-en/stream.m3u8",
                    "Utc": "2024-07-28T12:08:37.977Z"
                }
            ]
        }

**Attributes:**

.. list-table::
   :header-rows: 1

   * - Key
     - Path
     - Description
   * - Streams
     - ``Streams``
     - A list of audio streams
   * - Name
     - ``Streams.Name``
     - Name of the audio stream
   * - Language
     - ``Streams.Language``
     - Language of the audio stream
   * - Uri
     - ``Streams.Uri``
     - URL to access the audio stream
   * - Path
     - ``Streams.Path``
     - Path to the stream resource
   * - Utc
     - ``Streams.Utc``
     - UTC timestamp for the stream
    

Extrapolated Clock - :mod:`ExtrapolatedClock`
--------------------------------------

Predicts session time data:
- Remaining session time or laps.
- Calculations based on historical and current pace.

.. admonition:: Sample Request
    :class: warning

        https://livetiming.formula1.com/static/2024/2024-07-28_Belgian_Grand_Prix/2024-07-28_Race/ExtrapolatedClock.json

    .. tabs::

        .. code-tab:: shell

            curl "https://livetiming.formula1.com/static/2024/2024-07-28_Belgian_Grand_Prix/2024-07-28_Race/ExtrapolatedClock.json"

        .. code-tab:: python

            import requests

            url = "https://livetiming.formula1.com/static/2024/2024-07-28_Belgian_Grand_Prix/2024-07-28_Race/ExtrapolatedClock.json"
            response = requests.get(url)
            data = response.json()
            print(data)

        .. code-tab:: javascript

            fetch('https://livetiming.formula1.com/static/2024/2024-07-28_Belgian_Grand_Prix/2024-07-28_Race/ExtrapolatedClock.json')
                .then(response => response.json())
                .then(jsonContent => console.log(jsonContent));

.. admonition:: Response
    :class: info

    .. code-block:: json

        {
            "Utc": "2024-07-28T14:25:45.007Z",
            "Remaining": "00:38:07",
            "Extrapolating": true
        }

**Attributes:**

.. list-table::
   :header-rows: 1

   * - Key
     - Path
     - Description
   * - Utc
     - ``Utc``
     - Current time in UTC.
   * - Remaining
     - ``Remaining``
     - Time remaining in the session.
   * - Extrapolating
     - ``Extrapolating``
     - Indicates whether the clock is being extrapolated.

Tyre Stint Series - :mod:`TyreStintSeries`
--------------------------------------

Analyzes tyre usage over stints:
- Compound usage and wear rates.
- Strategy evaluation for tyre selection.

.. admonition:: Sample Request
    :class: warning

        https://livetiming.formula1.com/static/2024/2024-07-28_Belgian_Grand_Prix/2024-07-28_Race/TyreStintSeries.json

    .. tabs::

        .. code-tab:: shell

            curl "https://livetiming.formula1.com/static/2024/2024-07-28_Belgian_Grand_Prix/2024-07-28_Race/TyreStintSeries.json"

        .. code-tab:: python

            import requests
            url = "https://livetiming.formula1.com/static/2024/2024-07-28_Belgian_Grand_Prix/2024-07-28_Race/TyreStintSeries.json"
            response = requests.get(url)
            data = response.json()
            print(data)

        .. code-tab:: javascript

            fetch('https://livetiming.formula1.com/static/2024/2024-07-28_Belgian_Grand_Prix/2024-07-28_Race/TyreStintSeries.json')
                .then(response => response.json())
                .then(jsonContent => console.log(jsonContent));

.. admonition:: Response
    :class: info

    .. code-block:: json

        {
          "Stints": {
            "1": [
              {
                "Compound": "MEDIUM",
                "New": "true",
                "TyresNotChanged": "0",
                "TotalLaps": 10,
                "StartLaps": 0
              },
              {
                "Compound": "HARD",
                "New": "true",
                "TyresNotChanged": "0",
                "TotalLaps": 18,
                "StartLaps": 0
              }
            ],
            // Additional driver numbers and their stints...
          }
        }

**Attributes:**

.. list-table::
   :header-rows: 1

   * - Key
     - Path
     - Description
   * - Compound
     - ``Stints.<driver_number>.Compound``
     - Tyre compound used (SOFT, MEDIUM, or HARD)
   * - New
     - ``Stints.<driver_number>.New``
     - Boolean indicating if the tyres were new at the start of the stint
   * - TyresNotChanged
     - ``Stints.<driver_number>.TyresNotChanged``
     - Indicator if tyres were not changed during a pit stop
   * - TotalLaps
     - ``Stints.<driver_number>.TotalLaps``
     - Number of laps completed on this set of tyres
   * - StartLaps
     - ``Stints.<driver_number>.StartLaps``
     - Number of laps already done on the tyres when stint started

Session Status - :mod:`SessionStatus`
--------------------------------------

Displays the live session status:
- Current flag status (green, yellow, red).
- Notifications for major events.

.. admonition:: Sample Request
   :class: warning

       https://livetiming.formula1.com/static/2024/2024-07-28_Belgian_Grand_Prix/2024-07-28_Race/SessionStatus.json

   .. tabs::

       .. code-tab:: shell

           curl "https://livetiming.formula1.com/static/2024/2024-07-28_Belgian_Grand_Prix/2024-07-28_Race/SessionStatus.json"

       .. code-tab:: python

           import requests
           url = "https://livetiming.formula1.com/static/2024/2024-07-28_Belgian_Grand_Prix/2024-07-28_Race/SessionStatus.json"
           response = requests.get(url)
           data = response.json()
           print(data)

       .. code-tab:: javascript

           fetch('https://livetiming.formula1.com/static/2024/2024-07-28_Belgian_Grand_Prix/2024-07-28_Race/SessionStatus.json')
               .then(response => response.json())
               .then(jsonContent => console.log(jsonContent));

.. admonition:: Response
   :class: info

   .. code-block:: json

       {
         "Status": "Ends"
       }

**Attributes:**

.. list-table::
  :header-rows: 1

  * - Key
    - Path
    - Description
  * - Status
    - ``Status``
    - Current status of the session (e.g., "Ends", "Started", "Finished")


Timing Data - :mod:`TimingDataF1`
--------------------------------------

Specialized timing information for Formula 1:
- Sector times.
- Driver deltas and gaps.

.. admonition:: Sample Request
   :class: warning

       https://livetiming.formula1.com/static/2024/2024-07-28_Belgian_Grand_Prix/2024-07-28_Race/TimingDataF1.json

   .. tabs::

       .. code-tab:: shell

           curl "https://livetiming.formula1.com/static/2024/2024-07-28_Belgian_Grand_Prix/2024-07-28_Race/TimingDataF1.json"

       .. code-tab:: python

           import requests
           url = "https://livetiming.formula1.com/static/2024/2024-07-28_Belgian_Grand_Prix/2024-07-28_Race/TimingDataF1.json"
           response = requests.get(url)
           data = response.json()
           print(data)

       .. code-tab:: javascript

           fetch('https://livetiming.formula1.com/static/2024/2024-07-28_Belgian_Grand_Prix/2024-07-28_Race/TimingDataF1.json')
               .then(response => response.json())
               .then(jsonContent => console.log(jsonContent));

.. admonition:: Response
   :class: info

   .. code-block:: json

       {
         "Lines": {
           "1": {
             "GapToLeader": "+9.226",
             "IntervalToPositionAhead": {
               "Value": "+0.677",
               "Catching": true
             },
             "Line": 5,
             "Position": "5",
             "RacingNumber": "1",
             "Retired": false,
             "InPit": false,
             "NumberOfLaps": 44,
             "NumberOfPitStops": 2,
             "Sectors": [...],
             "Speeds": {
               "I1": {"Value": "334"},
               "I2": {"Value": "206"},
               "FL": {"Value": "223"},
               "ST": {"Value": "317"}
             },
             "BestLapTime": {
               "Value": "1:46.128",
               "Lap": 32
             },
             "LastLapTime": {
               "Value": "1:46.899"
             }
           },
           // Additional drivers...
         },
         "Withheld": false
       }

**Attributes:**

.. list-table::
  :header-rows: 1

  * - Key
    - Path
    - Description
  * - GapToLeader
    - ``Lines.<driver_number>.GapToLeader``
    - Time gap to the race leader
  * - IntervalToPositionAhead
    - ``Lines.<driver_number>.IntervalToPositionAhead.Value``
    - Time gap to the car in position ahead
  * - Catching
    - ``Lines.<driver_number>.IntervalToPositionAhead.Catching``
    - Boolean indicating if driver is catching the car ahead
  * - Position
    - ``Lines.<driver_number>.Position``
    - Current race position
  * - RacingNumber
    - ``Lines.<driver_number>.RacingNumber``
    - Driver's car number
  * - Retired
    - ``Lines.<driver_number>.Retired``
    - Boolean indicating if driver has retired from the race
  * - InPit
    - ``Lines.<driver_number>.InPit``
    - Boolean indicating if driver is currently in pit lane
  * - NumberOfLaps
    - ``Lines.<driver_number>.NumberOfLaps``
    - Total number of laps completed
  * - NumberOfPitStops
    - ``Lines.<driver_number>.NumberOfPitStops``
    - Total number of pit stops made
  * - Speeds.I1
    - ``Lines.<driver_number>.Speeds.I1.Value``
    - Speed at intermediate point 1 (km/h)
  * - Speeds.I2
    - ``Lines.<driver_number>.Speeds.I2.Value``
    - Speed at intermediate point 2 (km/h)
  * - Speeds.FL
    - ``Lines.<driver_number>.Speeds.FL.Value``
    - Speed at finish line (km/h)
  * - Speeds.ST
    - ``Lines.<driver_number>.Speeds.ST.Value``
    - Speed trap measurement (km/h)
  * - BestLapTime
    - ``Lines.<driver_number>.BestLapTime.Value``
    - Fastest lap time achieved
  * - BestLapTime Lap
    - ``Lines.<driver_number>.BestLapTime.Lap``
    - Lap number when best time was set
  * - LastLapTime
    - ``Lines.<driver_number>.LastLapTime.Value``
    - Time of the last completed lap

This endpoint provides comprehensive timing data for each driver during the race session, including positions, gaps, lap times, sector times, and speed measurements.

Timing Data (General)
--------------------------------------
**Topic:** TimingData

Generic timing data for the session:
- All racing categories.
- Laps and intervals.

Driver List - :mod:`DriverList`
--------------------------------------

Provides a list of active drivers:
- Car numbers and team names.
- Driver names and abbreviations.

Lap Series - :mod:`LapSeries`
--------------------------------------

Tracks laps completed:
- Lap times for each driver.
- Fastest lap indicators.

Top Three - :mod:`TopThree`
--------------------------------------

Highlights the top three drivers:
- Current positions.
- Time differences.

Timing Application Data - :mod:`TimingAppData`
--------------------------------------

Provides timing data from the Formula 1 application:
- Aggregated sector data.
- Driver gaps and intervals.

Timing Statistics - :mod:`TimingStats`
--------------------------------------

Analyzes timing data statistically:
- Averages, medians, and trends.
- Comparisons across sessions.

Heartbeat - :mod:`Heartbeat`
--------------------------------------

Regularly sends a system status signal:
- Ensures stream connectivity.
- Monitors data stream health.

Weather Data - :mod:`WeatherData`
--------------------------------------

Displays current weather conditions:
- Temperature, humidity, and wind.
- Rain predictions.

Weather Data Series - :mod:`WeatherDataSeries`
--------------------------------------

Offers historical weather data:
- Temperature trends.
- Rainfall patterns.

Position Data - :mod:`Position.z`
--------------------------------------

Tracks vertical position data:
- Insights into elevation changes.
- Vertical motion analysis.

Car Data - :mod:`CarData.z`
--------------------------------------

Analyzes car data along the Z axis:
- Suspension and vertical acceleration.

Team Audio and Race Control Messages - :mod:`TlaRcm`
--------------------------------------

Provides team audio and race control messages:
- Strategic communications.
- Official instructions and penalties.

Race Control Messages - :mod:`RaceControlMessages`
--------------------------------------

Broadcasts race control instructions:
- Penalties, warnings, and notes.
- Decisions affecting race outcomes.

Pit Lane Time Collection - :mod:`PitLaneTimeCollection`
--------------------------------------

Records pit lane timing data:
- Entry and exit times.
- Time spent in the pit lane.

Current Tyres - :mod:`CurrentTyres`
--------------------------------------

Details tyres currently in use:
- Compound type and condition.
- Wear levels and performance.

Driver Race Information - :mod:`DriverRaceInfo`
--------------------------------------

Provides individual driver performance metrics:
- Acceleration, speed, and fuel data.
- Driver-specific telemetry.

Team Radio - :mod:`TeamRadio`
--------------------------------------

Streams team radio communications:
- Real-time strategic discussions.
- Issue reporting and updates.

Championship Predictions - :mod:`ChampionshipPrediction`
--------------------------------------

Predicts championship outcomes:
- Based on current performance and standings.
- Statistical modeling and machine learning predictions.

Overtake Series - :mod:`OvertakeSeries`
--------------------------------------

Tracks overtakes during the session:
- Aggressive and defensive maneuvers.
- Key moments impacting race positions.

Driver Score - :mod:`DriverScore`
--------------------------------------

Calculates driver performance scores:
- Based on statistical and telemetry analysis.

Special Feed - :mod:`SPFeed`
--------------------------------------

Delivers a special data feed:
- Auxiliary metrics and session-specific insights.

Pit Stop Series - :mod:`PitStopSeries`
--------------------------------------

Tracks multiple pit stops:
- Strategy changes.
- Total pit stop durations.

Pit Stop - :mod:`PitStop`
--------------------------------------

Details individual pit stops:
- Entry and exit analysis.
- Errors and delays.

Lap Count - :mod:`LapCount`
--------------------------------------

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
