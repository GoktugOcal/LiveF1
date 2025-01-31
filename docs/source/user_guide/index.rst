User Guide
===========

Welcome to the **LiveF1 User Guide**! This guide will help you get started and walk you through the main features of the **LiveF1** package, covering both basic and advanced usage.

The Formula 1 Data
------------------

Formula 1 live timing data provides comprehensive insights into the performance of drivers, teams, and cars during races. This data is critical for real-time analytics, historical analysis, and developing strategies for races.

The live timing API follows a structured format to ensure efficient data access. Each API address corresponds to a specific endpoint, which streams or delivers data for various aspects of Formula 1 sessions. These endpoints can be accessed via HTTP requests.

.. tip::
   
   For more detailed information, refer to the :ref:`f1-livetiming-data` section.

Data Topics
^^^^^^^^^^^^^^^^^^

Understanding the data topics is crucial for retrieving the required data from the F1 Livestreaming API. Each topic corresponds to specific data points and endpoints, which are essential for accessing and analyzing the live timing data effectively.

.. tip::
   
   For the details of data topics, refer to the :ref:`data_topics` section.

General Functions
-----------------

This section will cover the general functions available in **LiveF1**, such as how to retrieve and interact with data like race sessions, teams, and driver stats. You’ll learn how to use the library’s core functions for both basic and advanced use cases.

.. list-table::
   :header-rows: 1

   * - Function
     - Description
   * - **get_season**
     - Retrieve data for a specific Formula 1 season. Usage Example: :ref:`get_season_example`
   * - **get_meeting**
     - Retrieve data for a specific meeting within a season. Usage Example: :ref:`get_meeting_example`
   * - **get_session**
     - Retrieve data for a specific session within a meeting and season. Usage Example: :ref:`get_session_example`
   * - **load_data**
     - Load and process data from a specific feed. Usage Example: :ref:`load_data_example`
   * - **get_laps**
     - Retrieve the laps data for a session. Usage Example: :ref:`get_laps_example`
   * - **get_car_telemetry**
     - Retrieve the car telemetry data for a session. Usage Example: :ref:`get_car_telemetry_example`
   * - **get_weather**
     - Retrieve the weather data for a session. Usage Example: :ref:`get_weather_example`
   * - **get_timing**
     - Retrieve the timing data for a session. Usage Example: :ref:`get_timing_example`

Working with Data
-----------------

In this section, you will find detailed instructions on how to load, process, and analyze F1 data using **LiveF1**. It will cover how to fetch data from different seasons, sessions, and data types, as well as how to handle both real-time and historical data.

(Topics to be filled later...)

.. toctree::
   :maxdepth: 1

   ../working_with_data/historical_data
   ../working_with_data/realtime_data