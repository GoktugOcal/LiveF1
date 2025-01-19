import pandas as pd

class BronzeLake:
    def __init__(self, session):
        self.session = session
        self.lake = {}

    def load_data(self, data_name):
        self.data = self.session.get_data(dataName=data_name)
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


class SilverLake:
    def __init__(self, bronze_lake):
        self.bronze_lake = bronze_lake
        self.data = None

    def load_data(self, data_name):
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


class GoldLake:
    def __init__(self, silver_lake):
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
        self.bronze_lake = BronzeLake(session=session)
        self.silver_lake = SilverLake(bronze_lake=self.bronze_lake)
        self.gold_lake = GoldLake(silver_lake=self.silver_lake)

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