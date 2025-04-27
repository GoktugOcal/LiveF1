import pandas as pd
from datetime import datetime

from ..utils.logger import logger
from ..utils.constants import TABLE_GENERATION_FUNCTIONS, TABLE_REQUIREMENTS
from .silver_functions import *
from .data_models import *

# class BronzeLake:
#     def __init__(self, session, great_lake):
#         self.great_lake = great_lake
#         self.lake = {}

#     def put(self, data_name, data):
#         """
#         Store the data in the BronzeLake.

#         Parameters
#         ----------
#         data_name : str
#             The name of the data to store.
#         data : object
#             The data to store.
#         """
        
#         self.lake[data_name] = data

#     def get(self, data_name):
#         """
#         Retrieve the data from the BronzeLake.

#         Parameters
#         ----------
#         data_name : str
#             The name of the data to retrieve.

#         Returns
#         -------
#         object
#             The requested data or None if it does not exist.
#         """
#         if self.has_data(data_name):
#             return self.lake[data_name]
#         else:
#             logger.info(f"Data '{data_name}' is not present in BronzeLake.")
#             return None

#     def has_data(self, data_name):
#         """
#         Check if the data exists in the BronzeLake.

#         Parameters
#         ----------
#         data_name : str
#             The name of the data to check.

#         Returns
#         -------
#         bool
#             True if the data exists, False otherwise.
#         """
#         return data_name in self.lake


# class SilverLake:
#     def __init__(self, great_lake, bronze_lake):
#         self.great_lake = great_lake
#         self.bronze_lake = bronze_lake
#         self.lake = {}

#     def get(self, data_name):
#         """
#         Retrieve the data from the SilverLake.

#         Parameters
#         ----------
#         data_name : str
#             The name of the data to retrieve.

#         Returns
#         -------
#         object
#             The requested data or None if it does not exist.
#         """
#         if self.has_data(data_name):
#             return self.lake[data_name]
#         else:
#             logger.info(f"Data '{data_name}' is not present in SilverLake.")
#             return None

#     def clean_data(self, data):
#         cleaned_data = []
#         for record in data:
#             cleaned_record = record  # Placeholder for actual cleaning logic
#             cleaned_data.append(cleaned_record)
#         return cleaned_data

#     def generate_table(self, table_name):
#         """
#         Generate a table using the corresponding function from silver_functions.py.

#         Parameters
#         ----------
#         table_name : str
#             The name of the table to generate.

#         Returns
#         -------
#         DataFrame
#             The generated table as a pandas DataFrame.
#         """
#         if table_name in TABLE_GENERATION_FUNCTIONS:
#             required_data = TABLE_REQUIREMENTS[table_name]
#             for data_name in required_data:
#                 if not self.bronze_lake.has_data(data_name):
#                     self.great_lake.session.get_data(data_name)
#             function_name = TABLE_GENERATION_FUNCTIONS[table_name]
#             return globals()[function_name](self.bronze_lake)
#         else:
#             raise ValueError(f"No generation function found for table: {table_name}")


# class GoldLake:
#     def __init__(self, great_lake, silver_lake):
#         self.great_lake = great_lake
#         self.silver_lake = silver_lake
#         self.lake = {}

#     def get(self, data_name):
#         """
#         Retrieve the data from the GoldLake.

#         Parameters
#         ----------
#         data_name : str
#             The name of the data to retrieve.

#         Returns
#         -------
#         object
#             The requested data or None if it does not exist.
#         """
#         if self.has_data(data_name):
#             return self.lake[data_name]
#         else:
#             logger.info(f"Data '{data_name}' is not present in GoldLake.")
#             return None

#     def aggregate_data(self, data):
#         aggregated_data = []
#         for record in data:
#             aggregated_record = record  # Placeholder for actual aggregation logic
#             aggregated_data.append(aggregated_record)
#         return aggregated_data


# class DataLake:
#     def __init__(self, session):
#         self.raw = {}
#         self.session = session
#         self.bronze_lake = BronzeLake(session=session, great_lake=self)
#         self.silver_lake = SilverLake(great_lake=self, bronze_lake=self.bronze_lake)
#         self.gold_lake = GoldLake(great_lake=self, silver_lake=self.silver_lake)

#     def load_data(self, level: str, data_name: str):
#         if level == "bronze":
#             return self.bronze_lake.get(data_name)
#         elif level == "silver":
#             return self.silver_lake.get(data_name)
#         elif level == "gold":
#             return self.gold_lake.get(data_name)
#         else:
#             raise ValueError("Invalid level. Must be one of 'bronze', 'silver', or 'gold'.")

#     def put(self, level, data_name, data):
#         """
#         Store the data in the DataLake.

#         Parameters
#         ----------
#         data_name : str
#             The name of the data to store.
#         data : object
#             The data to store.
#         """

#         if level == "bronze":
#             self.raw[data_name] = data.value
#             self.bronze_lake.put(data_name, data.df)
#         elif level == "silver":
#             pass
#         elif level == "gold":
#             pass
#         else:
#             raise ValueError("Invalid level. Must be one of 'bronze', 'silver', or 'gold'.")

#     def get(self, level: str, data_name: str):
#         """
#         Retrieve the data from the DataLake.

#         Parameters
#         ----------
#         level : str
#             The level of the lake ('bronze', 'silver', 'gold').
#         data_name : str
#             The name of the data to retrieve.

#         Returns
#         -------
#         object
#             The requested data or None if it does not exist.
#         """
#         if level == "bronze":
#             return self.bronze_lake.get(data_name)
#         elif level == "silver":
#             return self.silver_lake.get(data_name)
#         elif level == "gold":
#             return self.gold_lake.get(data_name)
#         else:
#             raise ValueError("Invalid level. Must be one of 'bronze', 'silver', or 'gold'.")


class BronzeLake:

    def __init__(self, session, great_lake):
        self.great_lake = great_lake
        self.lake = {}

    def put(self, table_name, table):
        """
        Store the data in the BronzeLake.

        Parameters
        ----------
        data_name : str
            The name of the data to store.
        bronze_table : object
            The data to store.
        """
        table.data_lake = self.great_lake
        self.lake[table_name] = table
        self.great_lake.update_metadata(table_name, "bronze")

    def get(self, table_name):
        """
        Retrieve the data from the BronzeLake.

        Parameters
        ----------
        data_name : str
            The name of the data to retrieve.

        Returns
        -------
        object
            The requested data or None if it does not exist.
        """
        if self.has_data(table_name):
            return self.lake[table_name]
        else:
            logger.info(f"Table '{table_name}' is not present in BronzeLake.")
            return None

    def has_data(self, table_name):
        """
        Check if the data exists in the BronzeLake.

        Parameters
        ----------
        data_name : str
            The name of the data to check.

        Returns
        -------
        bool
            True if the data exists, False otherwise.
        """
        return table_name in self.lake


class SilverLake:
    def __init__(self, great_lake, bronze_lake):
        self.great_lake = great_lake
        self.bronze_lake = bronze_lake
        self.lake = {}

    def put(self, table_name, table):
        """
        Store the data in the BronzeLake.

        Parameters
        ----------
        data_name : str
            The name of the data to store.
        bronze_table : object
            The data to store.
        """
        table.data_lake = self.great_lake
        self.lake[table_name] = table
        self.great_lake.update_metadata(table_name, "silver")

    def get(self, data_name):
        """
        Retrieve the data from the SilverLake.

        Parameters
        ----------
        data_name : str
            The name of the data to retrieve.

        Returns
        -------
        object
            The requested data or None if it does not exist.
        """
        if self.has_data(data_name):
            return self.lake[data_name]
        else:
            logger.info(f"Data '{data_name}' is not present in SilverLake.")
            return None

    def clean_data(self, data):
        cleaned_data = []
        for record in data:
            cleaned_record = record  # Placeholder for actual cleaning logic
            cleaned_data.append(cleaned_record)
        return cleaned_data

    # def generate_table(self, table_name):
    #     """
    #     Generate a table using the corresponding function from silver_functions.py.

    #     Parameters
    #     ----------
    #     table_name : str
    #         The name of the table to generate.

    #     Returns
    #     -------
    #     DataFrame
    #         The generated table as a pandas DataFrame.
    #     """
    #     if table_name in TABLE_GENERATION_FUNCTIONS:
    #         required_data = TABLE_REQUIREMENTS[table_name]
    #         for data_name in required_data:
    #             if not self.bronze_lake.has_data(data_name):
    #                 self.great_lake.session.get_data(data_name)
    #         function_name = TABLE_GENERATION_FUNCTIONS[table_name]
    #         return globals()[function_name](self.bronze_lake)
    #     else:
    #         raise ValueError(f"No generation function found for table: {table_name}")


class GoldLake:
    def __init__(self, great_lake, silver_lake):
        self.great_lake = great_lake
        self.silver_lake = silver_lake
        self.lake = {}

    def get(self, data_name):
        """
        Retrieve the data from the GoldLake.

        Parameters
        ----------
        data_name : str
            The name of the data to retrieve.

        Returns
        -------
        object
            The requested data or None if it does not exist.
        """
        if self.has_data(data_name):
            return self.lake[data_name]
        else:
            logger.info(f"Data '{data_name}' is not present in GoldLake.")
            return None

    def aggregate_data(self, data):
        aggregated_data = []
        for record in data:
            aggregated_record = record  # Placeholder for actual aggregation logic
            aggregated_data.append(aggregated_record)
        return aggregated_data


class DataLake:
    def __init__(self, session):
        self.session = session
        self.metadata = {}

        self.bronze = BronzeLake(session=session, great_lake=self)
        self.silver = SilverLake(great_lake=self, bronze_lake=self.bronze)
        self.gold = GoldLake(great_lake=self, silver_lake=self.silver)
    
    def update_metadata(self, table_name, level):
        if level == "bronze": created_at = datetime.now()
        else: created_at = None

        self.metadata[table_name] = {
            "table_type": level,
            "created_at": created_at
        }
    
    def put(self, level, table_name, table):
        """
        Store the data in the DataLake.

        Parameters
        ----------
        data_name : str
            The name of the data to store.
        data : object
            The data to store.
        """

        if level == "bronze":
            self.bronze.put(table_name, table)
        elif level == "silver":
            self.silver.put(table_name, table)
        elif level == "gold":
            pass
        else:
            raise ValueError("Invalid level. Must be one of 'bronze', 'silver', or 'gold'.")
    
    def get(self, level: str, table_name: str):
        """
        Retrieve the data from the DataLake.

        Parameters
        ----------
        level : str
            The level of the lake ('bronze', 'silver', 'gold').
        data_name : str
            The name of the data to retrieve.

        Returns
        -------
        object
            The requested data or None if it does not exist.
        """
        if level == "bronze":
            return self.bronze.get(table_name)
        elif level == "silver":
            return self.silver.get(table_name)
        elif level == "gold":
            return self.gold.get(table_name)
        else:
            raise ValueError("Invalid level. Must be one of 'bronze', 'silver', or 'gold'.")
    
    # def create_silver_table(self, source_tables, table_name):
    #     """
    #     Decorator factory that creates a SilverTable instance
        
    #     Args:
    #         source_tables: List of source tables to use (BronzeTable instances in BronzeLake)
    #         table_name: Optional name for the table, defaults to function name if None
    #     """
    #     def decorator(callback_func):
    #         # Create a new SilverTable instance
    #         table = SilverTable(table_name, sources=source_tables)
    #         table.callback = callback_func
            
    #         # # Set the create_table method to run the callback
    #         # def create_table_wrapper():
    #         #     return table.create_table()
            
    #         # # Add the create_table method to the returned object
    #         # callback_func.create_table = create_table_wrapper
    #         # callback_func.table = table
            
    #         print("putting table to silver lake...")
    #         self.put(level="silver", table_name=table_name, table=table)
    #         return callback_func
        
    #     return decorator


    def create_bronze_table(self, table_name, raw_data, parsed_data):
        """
        Decorator factory that creates a BronzeTable instance
        
        Args:
            source_tables: List of source tables to use (BronzeTable instances in BronzeLake)
            table_name: Optional name for the table, defaults to function name if None
        """
        self.put(
            level="bronze",
            table_name=table_name,
            table= BronzeTable(
                table_name=table_name,
                data=raw_data,  
                parsed_data=parsed_data
            )
        )

    # def create_silver_table(self, table_name, source_tables):

    #     silver_table = SilverTable(
    #         table_name=table_name,
    #         sources=source_tables
    #     )

    #     self.put(
    #         level="silver",
    #         table_name=table_name,
    #         table=silver_table
    #     )

    #     return silver_table

    def generate_silver_table(self, table_name):
        """
        Generate a silver table from a bronze tables
        """
        self.silver.lake[table_name].generate_table()






