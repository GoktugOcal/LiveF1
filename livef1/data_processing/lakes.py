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

class SimpleLake:
    def __init__(self, great_lake):
        self.great_lake = great_lake
        self.lake = {}
        self.lake_type = None
    
    def put(self, table_name, table):
        """
        Store the data in the Lake.

        Parameters
        ----------
        data_name : str
            The name of the data to store.
        bronze_table : object
            The data to store.
        """
        table.data_lake = self.great_lake
        self.lake[table_name] = table
        self.great_lake.update_metadata(
            table_name = table_name,
            level = self.lake_type,
            created_at = datetime.now()
            )

    def get(self, table_name):
        """
        Retrieve the data from the Lake.

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
        Check if the data exists in the Lake.

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
            

class BronzeLake(SimpleLake):
    def __init__(self, great_lake):
        super().__init__(great_lake)
        self.lake_type = "bronze"

class SilverLake(SimpleLake):
    def __init__(self, great_lake):
        super().__init__(great_lake)
        self.lake_type = "silver"

class GoldLake(SimpleLake):
    def __init__(self, great_lake):
        super().__init__(great_lake)
        self.lake_type = "gold"


class DataLake:
    def __init__(self, session):
        self.session = session
        self.metadata = {}

        self.bronze = BronzeLake(great_lake=self)
        self.silver = SilverLake(great_lake=self)
        self.gold = GoldLake(great_lake=self)
    
    def update_metadata(
        self,
        table_name,
        level,
        created_at=None,
        generated=False
        ):

        if table_name in self.metadata:
            self.metadata[table_name] = {
                "table_type": level if level else self.metadata[table_name]["table_type"],
                "created_at": created_at if created_at else self.metadata[table_name]["created_at"],
                "generated" : generated if generated else self.metadata[table_name]["generated"]
            }
        
        else:
            self.metadata[table_name] = {
                "table_type": level,
                "created_at": created_at,
                "generated" : generated
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
            self.gold.put(table_name, table)
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
    
    def _identify_table_level(self, table_name):
        """
        Identify the level of a table
        """
        if table_name in self.metadata:
            return self.metadata[table_name]["table_type"]
        else:
            table_level = self.session._identify_data_level(table_name)
            if table_level:
                return table_level
            else:
                return None
            

    def _check_circular_dependencies(self):
        """
        Check for circular dependencies in the tables across different levels.
        
        This method detects cycles in the dependency graph of tables, which would
        make it impossible to generate tables in a valid order.
        
        Returns
        -------
        bool
            True if no circular dependencies exist, False otherwise.
        
        Raises
        ------
        ValueError
            If circular dependencies are detected, with details about the cycle.
        """
        # Track visited tables and current path during DFS
        visited = set()
        path = set()
        path_list = []
        
        def dfs(table):
            """Depth-first search to detect cycles in the dependency graph."""
            # If we've already fully explored this node, no need to check again
            if table in visited:
                return True
            
            # If we encounter a table already in our current path, we have a cycle
            table_name = table.table_name
            if table_name in path:
                cycle_start = path_list.index(table_name)
                cycle = path_list[cycle_start:] + [table_name]
                raise ValueError(f"Circular dependency detected: {' -> '.join(cycle)}")
            
            # Add current table to path
            path.add(table_name)
            path_list.append(table_name)
            
            # If table has dependency_tables attribute, check those too
            if hasattr(table, 'dependency_tables') and table.dependency_tables:
                for dep_table in table.dependency_tables:
                    # dependency_tables contains actual table objects
                    dep_table_name = dep_table.table_name
                    if not dfs(dep_table):
                        return False
            
            # Remove from current path and mark as visited
            path.remove(table_name)
            path_list.pop()
            visited.add(table_name)
            return True
        
        # Start DFS from all tables in the metadata
        for table_name, info in self.metadata.items():
            if info["table_type"] in ["silver", "gold"] and table_name not in visited:
                table = self.get(info["table_type"], table_name)
                if not dfs(table):
                    return False
        
        return True


    def generate_silver_table(self, table_name):
        """
        Generate a silver table from a bronze tables
        """
        self.silver.lake[table_name].generate_table()






