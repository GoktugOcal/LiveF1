*******************
Data Objects
*******************

.. _get_season:
Season
======

The `Season` class represents a Formula 1 season, containing methods to load and manage the season's meetings and sessions.

Example:

.. code-block:: python

    from livef1.models.season import Season

    # Initialize a season for the year 2023
    season_2023 = Season(year=2023, meetings=[])

    # Load the season data
    season_2023.load()

    # Access the meetings
    meetings = season_2023.meetings

.. _get_meeting:
Meeting
=======

The `Meeting` class represents a meeting in a specific season with relevant details and associated sessions.

Example:

.. code-block:: python

    from livef1.models.meeting import Meeting

    # Initialize a meeting
    meeting = Meeting(season=season_2023, year=2023, location="Monaco")

    # Load the meeting data
    meeting.load()

    # Access the sessions
    sessions = meeting.sessions

.. _get_session:
Session
=======

The `Session` class represents a Formula 1 session, containing methods to retrieve live timing data and process it.

Example:

.. code-block:: python

    from livef1.models.session import Session

    # Initialize a session
    session = Session(season=season_2023, meeting=meeting, name="Practice 1")

    # Get topic names
    topic_names = session.get_topic_names()

    # Load data for a specific topic
    data = session.load_data(dataName="Car_Data")

Generating Data
===============

The `generate` method in the `Session` class is used to generate and save processed data tables (silver and gold tables) for the session. This is useful for organizing and accessing detailed session data efficiently.

Example:

.. code-block:: python

    # Generate silver tables for the session
    session.generate(silver=True, gold=False)

    # Access the generated data
    laps = session.get_laps()
    telemetry = session.get_car_telemetry()
    weather = session.get_weather()
    timing = session.get_timing()

Why Run `.generate`
===================

Running the `.generate` method is important for the following reasons:

1. **Data Organization**: It organizes raw data into structured tables, making it easier to analyze and visualize.
2. **Efficiency**: Preprocessing and storing data in tables reduces the need for repeated data parsing and processing.
3. **Accessibility**: Generated tables can be accessed directly through the session object, simplifying data retrieval.


.. automodule:: livef1
    :undoc-members:
    :inherited-members:
   
    .. autosummary::
        models.Season
        models.Meeting
        models.Session