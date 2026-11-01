Medallion Architecture - :mod:`livef1.data_processing.lake`
=================================

Data Lakes
-------------------
.. automodule:: livef1.data_processing.lakes
   :members: BasicResult

    .. rubric:: Classes
    .. autosummary::
        DataLake
        BronzeLake
        SilverLake
        GoldLake


Silver Table Generation Functions
--------------------
.. automodule:: livef1.data_processing.silver_functions
   :undoc-members:
   :inherited-members:
   
   .. rubric:: Functions
   .. autosummary::    
        generate_laps_table
        generate_car_telemetry_table
        generate_race_control_messages_table


Silver Table Generation Functions (Polars)
------------------------------------------
Used when ``livef1.configure(dataframe_backend="polars")`` is set.

.. automodule:: livef1.data_processing.silver_functions_polars
   :members: generate_laps_table, generate_car_telemetry_table, generate_race_control_messages_table

   .. rubric:: Functions
   .. autosummary::
        generate_laps_table
        generate_car_telemetry_table
        generate_race_control_messages_table