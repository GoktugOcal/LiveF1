import pandas as pd
from livef1.utils.constants import column_mapping
import livef1

class Table:
    def __init__(self, data_lake, table_name):
        self.data_lake = data_lake
        self.table_name = table_name
        self.table = None
        self.callback = None
        self.df = None
    
    def create_table(self):
        if self.callback:
            self.df = self.callback(self)
        return self.df

class BronzeTable(Table):
    def __init__(self, data_lake, table_name, data):
        super().__init__(data_lake, table_name)
        self.raw = data
        self.df = pd.DataFrame(data).rename(
            columns = column_mapping
        )

class SilverTable(Table):
    def __init__(self, data_lake, table_name, sources):
        super().__init__(data_lake, table_name)
        self.sources = sources
        self.df = None

    

class DataLake:
    def __init__(self, session):
        self.raw = {}
        self.bronze = []
        self.silver = []
        self.gold = []
        self.session = session
    def add_bronze_table(self, table):
        self.bronze.append(table)

    def add_silver_table(self, table):
        self.silver.append(table)
    
    def create_silver_table(self, source_tables, table_name):
        """
        Decorator factory that creates a SilverTable instance
        
        Args:
            source_tables: List of source tables to use (BronzeTable instances in BronzeLake)
            table_name: Optional name for the table, defaults to function name if None
        """
        def decorator(callback_func):
            # Use provided table_name or function name if not provided
            actual_table_name = table_name or callback_func.__name__
            # Create a new SilverTable instance
            table = SilverTable(actual_table_name)
            table.sources = source_tables
            table.callback = callback_func
            
            # Set the create_table method to run the callback
            def create_table_wrapper():
                return table.create_table()
            
            # Add the create_table method to the returned object
            callback_func.create_table = create_table_wrapper
            callback_func.table = table
            
            self.add_silver_table(table)
            return callback_func
        
        return decorator


    def create_bronze_table(self, table_name, topic_name):
        """
        Decorator factory that creates a BronzeTable instance
        
        Args:
            source_tables: List of source tables to use (BronzeTable instances in BronzeLake)
            table_name: Optional name for the table, defaults to function name if None
        """

        data = self.session.get_data(topic_name)
        table = BronzeTable(self, table_name, data)
        self.add_bronze_table(table)



session = livef1.get_session(2025, "Jeddah", "Race")
data_lake = DataLake(session)

data_lake.create_bronze_table("SessionData", "SessionData")

df = data_lake.bronze[0]
print(df)