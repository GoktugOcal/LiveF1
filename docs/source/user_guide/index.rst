User Guide
===========

Welcome to the **LiveF1 User Guide**! This guide will help you understand how to effectively use the LiveF1 package for accessing and analyzing Formula 1 timing data. Whether you're interested in real-time race analytics or historical data analysis, this guide will walk you through the essential concepts and features.

Understanding Formula 1 Data
---------------------------

Formula 1 live timing data provides comprehensive insights into the performance of drivers, teams, and cars during races. This data is critical for real-time analytics, historical analysis, and developing strategies for races.

The live timing API follows a structured format to ensure efficient data access. Each API address corresponds to a specific endpoint, which streams or delivers data for various aspects of Formula 1 sessions. These endpoints can be accessed via HTTP requests.

.. seealso::
   For detailed information about the F1 timing data structure and available endpoints, see :ref:`f1-livetiming-data`.

The LiveF1 package organizes this data using the :ref:`medallion_architecture`, which structures data into Bronze (raw), Silver (cleaned), and Gold (analytics-ready) layers.

Core Concepts
------------

Before diving into specific features, it's important to understand these key concepts:

1. **Data Organization**

   - Seasons contain multiple race meetings
   - Meetings contain multiple sessions (Practice, Qualifying, Race)
   - Sessions contain various data feeds (telemetry, timing, weather, etc.)

2. **Data Access Patterns**

   - Historical data access for past races
   - Real-time data streaming for live sessions
   - Data transformation through the medallion architecture

3. **Data Types**

   - Each session provides multiple data feeds, organized by topics like car telemetry, position data, and timing information.

.. tip::
   Browse available data topics and their descriptions in :ref:`data_topics`.

Getting Started with Data
------------------------

The package provides three main functions for accessing F1 data:

1. :ref:`get_season`: Access an entire F1 season
2. :ref:`get_meeting`: Access a specific race meeting
3. :ref:`get_session`: Access a specific session

Once you have a session object, you can:

- Load raw data using ``get_data()``
- Generate processed tables using ``generate()``
- Access specific data types through attributes like ``laps``, ``carTelemetry``, etc. The attribute names are defined while registering tables; have a look at :ref:`registering_custom_tables`.

Examples and Use Cases
---------------------

- :ref:`historical_data`: Learn how to analyze past race data
- :ref:`realtime_data`: Learn how to work with live session data
- :ref:`quick_start`: Quick examples to get started

Where to Go Next
---------------

* For detailed API documentation, see the :ref:`api_reference`
* For examples and tutorials, check out the :ref:`examples` section
* For understanding data organization, read about the :ref:`medallion_architecture`
* For available data feeds, browse the :ref:`data_topics`

.. .. toctree::
..    :maxdepth: 2
..    :hidden:

..    medallion_architecture
..    data_objects
..    data_models
..    historical_data
..    realtime_data