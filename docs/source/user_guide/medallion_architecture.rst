Medallion Architecture
======================

The Medallion Architecture is a data processing architecture that organizes data into different layers or "lakes" based on their level of refinement. The three primary layers are Bronze, Silver, and Gold.

Bronze Layer
------------
This is the raw data layer where data is ingested in its original format. It serves as the single source of truth and is typically unprocessed. The main advantage of the Bronze Layer is that it allows for the storage of data in its most granular form, ensuring that no information is lost. This layer is crucial for data traceability and auditing, as it provides a complete and unaltered record of the ingested data.

Silver Layer
------------
This layer contains cleaned and enriched data. Data in this layer has undergone some transformation and validation to ensure quality and consistency. The Silver Layer is essential for improving data quality by removing duplicates, correcting errors, and standardizing formats. This layer also enables the integration of data from multiple sources, providing a unified view of the data. By processing data in the Silver Layer, organizations can ensure that downstream applications and analytics are based on reliable and accurate data.

Gold Layer
----------
This is the final layer where data is aggregated and optimized for analytics and reporting. Data in this layer is highly refined and ready for business intelligence and machine learning applications. The Gold Layer provides high-performance access to data, enabling fast and efficient querying and analysis. This layer is designed to support complex analytical workloads and deliver insights that drive business decisions. By organizing data in the Gold Layer, organizations can ensure that their analytics and reporting are based on the most relevant and up-to-date information.

Schema of the Table System
--------------------------
Below is a schema representing the Medallion Architecture in the context of the `Session` class:

.. code-block:: plaintext

    +-------------------+       +-------------------+       +-------------------+
    |   Bronze Layer    |       |   Silver Layer    |       |    Gold Layer     |
    | (Raw Data Storage)|       | (Cleaned & Enriched)|     | (Aggregated & Optimized)|
    +-------------------+       +-------------------+       +-------------------+
    | - TimingData      |       | - Laps Table      |       | - Aggregated Data |
    | - CarData         |       | - Car Telemetry   |       | - Analytics Ready |
    | - PositionData    |       | - Weather Data    |       | - Reporting Ready |
    +-------------------+       +-------------------+       +-------------------+

Benefits of Medallion Architecture
----------------------------------
The Medallion Architecture ensures high data quality through multiple layers of transformation and validation. By processing data in stages, organizations can systematically improve data quality and consistency. The architecture allows for the addition of new data sources and processing steps without disrupting existing workflows, making it highly scalable. This flexibility enables organizations to adapt to changing data requirements and integrate new data sources seamlessly.

The architecture enables parallel development and faster iteration by allowing different teams to work on different layers independently. This modular approach reduces dependencies and accelerates the development process. It maintains a clear lineage of data transformations, making it easier to trace and debug issues. Data lineage is crucial for compliance and auditing, as it provides a transparent view of how data has been processed and transformed.

By optimizing data at each layer, the architecture improves query performance and reduces the load on downstream systems. This optimization ensures that analytical queries are executed efficiently, providing faster insights and reducing infrastructure costs.

In the context of the `Session` class, the Medallion Architecture helps in organizing and processing live timing data efficiently. The `BronzeLake` stores raw data, which can be quickly retrieved and processed as needed. This ensures that the original data is always available for reference and auditing. The `SilverLake` layer processes and enriches the raw data, making it more useful for analysis. By cleaning and standardizing the data, the Silver Layer ensures that the analysis is based on high-quality data.

The `GoldLake` layer aggregates and optimizes data for advanced analytics and reporting. This layer provides fast and efficient access to data, enabling complex analytical queries and reporting. Each layer can be processed independently, allowing for modular and maintainable code. This modularity simplifies the development and maintenance of the `Session` class, enabling faster iteration and reducing the risk of errors.

Example Usage
-------------
Here are some examples of how the Medallion Architecture is used in the `Session` class. The `load_data` method retrieves raw data from the `BronzeLake`. The `generate` method processes raw data to create enriched tables in the `SilverLake`. Methods like `get_laps` and `get_car_telemetry` retrieve refined data from the `SilverLake`.