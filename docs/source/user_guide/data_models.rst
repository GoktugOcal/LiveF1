Data Models
==========

Season
------
The Season model is the top-level container for Formula 1 data. It manages all meetings and sessions for a specific year.

**Key Attributes:**
- ``year``: The F1 season year
- ``meetings``: List of Meeting objects
- ``meetings_json``: Raw meeting data
- ``season_table``: Pandas DataFrame with season data
- ``meetings_table``: Aggregated meetings data

**Example Usage:**

.. code-block:: python

    import livef1

    # Get a season
    season = livef1.get_season(2024)
    
    # Access meetings
    print(season.meetings_table)  # View all meetings
    print(season.meetings)  # Access Meeting objects

    # Get specific meeting
    monaco_gp = [m for m in season.meetings if m.location == "Monaco"][0]

Meeting
-------
The Meeting model represents a specific Grand Prix event within a season. It manages session data and meeting metadata.

**Key Attributes:**
- ``season``: Reference to parent Season object
- ``code``: Meeting code (e.g., "MON")
- ``key``: Unique identifier
- ``location``: Circuit location
- ``name``: Grand Prix name
- ``sessions``: List of Session objects
- ``sessions_table``: DataFrame of session data

**Example Usage:**

.. code-block:: python

    # Get specific meeting
    meeting = livef1.get_meeting(
        season=2024,
        meeting_identifier="Monaco"
    )

    # Access sessions
    print(meeting.sessions_table)  # View all sessions
    
    # Get specific session
    race = [s for s in meeting.sessions if s.type == "Race"][0]

Session
-------
The Session model represents individual F1 sessions (Practice, Qualifying, Race) and implements the medallion architecture for data processing.

**Key Attributes:**
- ``meeting``: Reference to parent Meeting object
- ``type``: Session type (e.g., "Race", "Practice 1")
- ``name``: Session name
- ``key``: Unique identifier
- ``startdate``: Session start time
- ``enddate``: Session end time
- ``data_lake``: DataLake object for data storage
- ``topic_names_info``: Available data topics

**Data Access Methods:**
- ``get_data()``: Retrieve raw data
- ``generate()``: Create processed tables
- ``get_laps()``: Access lap data
- ``get_car_telemetry()``: Access telemetry data

**Example Usage:**

.. code-block:: python

    # Get specific session
    session = livef1.get_session(
        season=2024,
        meeting_identifier="Monaco",
        session_identifier="Race"
    )

    # Load raw data
    telemetry = session.get_data("CarData.z")
    
    # Generate processed tables
    session.generate(silver=True)
    
    # Access processed data
    laps = session.get_laps()
    telemetry = session.get_car_telemetry()

Data Flow
---------
The models work together in a hierarchical structure:

.. code-block:: text

    Season
    ├── Meeting 1
    │   ├── Practice 1
    │   ├── Practice 2
    │   ├── Practice 3
    │   ├── Qualifying
    │   └── Race
    ├── Meeting 2
    │   └── ...
    └── Meeting N
        └── ...

Each level provides specific functionality:

1. **Season Level**
   - Season-wide data access
   - Meeting management
   - High-level data organization

2. **Meeting Level**
   - Session management
   - Meeting-specific data
   - Circuit information

3. **Session Level**
   - Raw data access
   - Data processing
   - Medallion architecture implementation

Best Practices
-------------
1. **Data Access**
   - Use high-level functions (``get_season()``, ``get_meeting()``, ``get_session()``)
   - Access objects through their parent when possible
   - Use data frames for bulk data analysis

2. **Data Processing**
   - Generate silver tables before accessing processed data
   - Use parallel processing for multiple data topics
   - Cache frequently accessed data

3. **Memory Management**
   - Load data only when needed
   - Use data lake for persistent storage
   - Clear unused data from memory

.. seealso::
   - For more details on data processing, see :ref:`medallion_architecture`
   - For API documentation, see :ref:`api_reference`
