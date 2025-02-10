.. _medallion_architecture:
Medallion Architecture
======================

LiveF1 implements a three-layer data processing architecture known as the Medallion Architecture. This design pattern organizes data into Bronze (raw), Silver (cleaned), and Gold (analytics-ready) layers, ensuring data quality and efficient processing.

.. grid:: 3
   :gutter: 2
   :class-container: sd-text-center

   .. grid-item-card:: Bronze Layer
      :img-top: ../_static/bronze.png
      :class-card: sd-border-0

      Raw data ingestion
      Raw logs and records
      Single source of truth

   .. grid-item-card:: Silver Layer  
      :img-top: ../_static/silver.png
      :class-card: sd-border-0

      Cleaned & enriched data
      Standardized formats
      Quality assured

   .. grid-item-card:: Gold Layer
      :img-top: ../_static/gold.png 
      :class-card: sd-border-0

      Analytics-ready data
      Optimized queries
      Business metrics

Data Flow Architecture
---------------------

.. code-block:: text
   :caption: Data Flow Diagram
   :class: no-copybutton

    Raw Data Sources                    Processing Layers                   Consumption
    ┌──────────────┐     ┌────────────┐     ┌────────────┐     ┌────────────┐     ┌──────────────┐
    │   F1 Live    │     │            │     │            │     │            │     │  Analytics   │
    │   Timing    ─┼────►│   Bronze   │────►│   Silver   │────►│    Gold    │────►│  Dashboards  │
    │              │     │    Lake    │     │    Lake    │     │    Lake    │     │              │
    └──────────────┘     └────────────┘     └────────────┘     └────────────┘     └──────────────┘
                               │                  │                   │
                               ▼                  ▼                   ▼
                            Raw Storage      Cleaned Data        Aggregated
                            JSON Files       Pandas Tables      Analytics Data


Layer Details
------------

Bronze Layer (Raw Data)
^^^^^^^^^^^^^^^^^^^^^^

The Bronze layer stores data in its original format, serving as the foundation of our data lake.

.. code-block:: python
   :caption: Example: Loading Raw Data
   :emphasize-lines: 4

    # Get raw timing data
    session = livef1.get_session(2024, "Spa", "Race")
    
    raw_data = session.get_data("TimingData")  # Loads to Bronze lake
    print(raw_data.head())

.. admonition:: Key Features
   :class: note

   - Unmodified source data
   - Complete data history
   - Audit trail support
   - Quick ingestion
   - Schema-on-read

Silver Layer (Refined Data) 
^^^^^^^^^^^^^^^^^^^^^^^^^

The Silver layer contains cleaned, validated, and enriched data ready for analysis.

.. code-block:: python
   :caption: Example: Generating Silver Tables
   :emphasize-lines: 4,7

    # Generate silver layer tables
    session = livef1.get_session(2024, "Spa", "Race")
    
    session.generate(silver=True)  # Process Bronze to Silver
    
    # Access refined data
    laps_data = session.get_laps()  # Get from Silver lake
    print(laps_data.head())

.. admonition:: Data Quality Checks
   :class: tip

   - Data type validation
   - Duplicate removal
   - Missing value handling
   - Format standardization
   - Cross-reference validation

Gold Layer (Analytics Ready)
^^^^^^^^^^^^^^^^^^^^^^^^

The Gold layer provides optimized, aggregated data ready for business intelligence and machine learning.

.. code-block:: python
   :caption: Example: Accessing Gold Layer Data
   :emphasize-lines: 4

    # Generate gold metrics 
    session = livef1.get_session(2024, "Spa", "Race")
    session.generate(silver=True, gold=True)
    
    aggregated_data = session.get_gold_metrics()  # Access Gold lake

.. admonition:: Optimizations
   :class: tip

   - Pre-calculated aggregations
   - Optimized query patterns
   - Business metrics
   - ML-ready features
   - Performance tuning

Implementation Details
--------------------

Data Lake Structure
^^^^^^^^^^^^^^^^^

The data lake implementation in LiveF1 uses a class-based structure:

.. code-block:: text

    session.data_lake/
    ├── bronze/                 # Raw data storage
    │   ├── timing/            # Timing data
    │   ├── telemetry/         # Car telemetry 
    │   └── weather/           # Weather data
    │
    ├── silver/                # Cleaned data
    │   ├── laps/             # Lap time analysis
    │   ├── car_data/         # Processed telemetry
    │   └── track_status/     # Track conditions
    │
    └── gold/                  # Analytics data
        ├── performance/       # Performance metrics
        ├── strategy/         # Strategy insights
        └── predictions/      # ML predictions

Processing Methods
^^^^^^^^^^^^^^^^^^^

LiveF1 provides methods for processing data through each layer:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Method
     - Description
   * - ``get_data()``
     - Loads raw data into Bronze layer
   * - ``generate(silver=True)``
     - Processes data to Silver layer
   * - ``generate(gold=True)``
     - Creates Gold layer analytics
   * - ``get_laps()``
     - Retrieves lap data from Silver
   * - ``get_telemetry()``
     - Accesses processed telemetry

Best Practices
-------------

When working with the Medallion Architecture in LiveF1:

1. **Data Loading**
   - Always load raw data to Bronze first
   - Use parallel loading for multiple feeds
   - Implement error handling

2. **Data Processing**
   - Generate Silver tables as needed
   - Cache frequently used data
   - Monitor processing time

3. **Data Access**
   - Use appropriate layer for needs
   - Implement data validation
   - Follow access patterns

.. seealso::
   - :ref:`data_topics` for available data feeds
   - :ref:`api_reference` for detailed API documentation

Next Steps
---------

- Learn about :ref:`data_objects` in LiveF1
- Explore :ref:`examples` for practical usage
- Read about :ref:`quick_start` for getting started