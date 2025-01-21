import pandas as pd
from ..utils.logger import logger
from ..utils.constants import TABLE_GENERATION_FUNCTIONS, TABLE_REQUIREMENTS
from .silver_functions import *
from .data_models import *

class BronzeLake:
    def __init__(self, session, great_lake):
        self.great_lake = great_lake
        self.lake = {}

    def load_data(self, data_name):
        self.data = self.great_lake.session.get_data(dataName=data_name)
        return BronzeResult(data=self.data.value)

    def put(self, data_name, data):
        """
        Store the data in the BronzeLake.

        Parameters
        ----------
        data_name : str
            The name of the data to store.
        data : object
            The data to store.
        """
        
        self.lake[data_name] = data

    def get(self, data_name):
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
        if self.has_data(data_name):
            return self.lake[data_name]
        else:
            logger.info(f"Data '{data_name}' is not present in BronzeLake.")
            return None

    def has_data(self, data_name):
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
        return data_name in self.lake


class SilverLake:
    def __init__(self, great_lake, bronze_lake):
        self.great_lake = great_lake
        self.bronze_lake = bronze_lake
        self.data = None

    def load_data(self, data_name):
        if data_name in TABLE_GENERATION_FUNCTIONS:
            function_name = TABLE_GENERATION_FUNCTIONS[data_name]
            self.data = globals()[function_name](self.bronze_lake)
        else:
            if not self.bronze_lake.data:
                self.bronze_lake.load_data(data_name)
            self.data = self.clean_data(self.bronze_lake.data.value)
        return SilverResult(data=self.data)

    def clean_data(self, data):
        cleaned_data = []
        for record in data:
            cleaned_record = record  # Placeholder for actual cleaning logic
            cleaned_data.append(cleaned_record)
        return cleaned_data

    def generate_table(self, table_name):
        """
        Generate a table using the corresponding function from silver_functions.py.

        Parameters
        ----------
        table_name : str
            The name of the table to generate.

        Returns
        -------
        DataFrame
            The generated table as a pandas DataFrame.
        """
        if table_name in TABLE_GENERATION_FUNCTIONS:
            required_data = TABLE_REQUIREMENTS.get(table_name, [])
            for data_name in required_data:
                if not self.bronze_lake.has_data(data_name):
                    self.bronze_lake.load_data(data_name)
            function_name = TABLE_GENERATION_FUNCTIONS[table_name]
            return globals()[function_name](self.bronze_lake)
        else:
            raise ValueError(f"No generation function found for table: {table_name}")


class GoldLake:
    def __init__(self, great_lake, silver_lake):
        self.great_lake = great_lake
        self.silver_lake = silver_lake
        self.data = None

    def load_data(self, data_name):
        if not self.silver_lake.data:
            self.silver_lake.load_data(data_name)
        self.data = self.aggregate_data(self.silver_lake.data)
        return GoldResult(data=self.data)

    def aggregate_data(self, data):
        aggregated_data = []
        for record in data:
            aggregated_record = record  # Placeholder for actual aggregation logic
            aggregated_data.append(aggregated_record)
        return aggregated_data


class DataLake:
    def __init__(self, session):
        self.raw = {}
        self.session = session
        self.bronze_lake = BronzeLake(session=session, great_lake=self)
        self.silver_lake = SilverLake(great_lake=self, bronze_lake=self.bronze_lake)
        self.gold_lake = GoldLake(great_lake=self, silver_lake=self.silver_lake)

    def load_data(self, level: str, data_name: str):
        if level == "bronze":
            res = self.bronze_lake.load_data(data_name)

            return 
        elif level == "silver":
            return self.silver_lake.load_data(data_name)
        elif level == "gold":
            return self.gold_lake.load_data(data_name)
        else:
            raise ValueError("Invalid level. Must be one of 'bronze', 'silver', or 'gold'.")

    def put(self, data_name, data):
        """
        Store the data in the DataLake.

        Parameters
        ----------
        data_name : str
            The name of the data to store.
        data : object
            The data to store.
        """
        self.raw[data_name] = data.value
        self.bronze_lake.put(data_name, pd.DataFrame(data.value))