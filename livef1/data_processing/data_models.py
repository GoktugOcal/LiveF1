# Standard Library Imports
import json
from datetime import datetime

# Third-Party Library Imports
import pandas as pd
from ..utils.constants import column_mapping


class BasicResult:
    """
    Encapsulates a basic result dataset, typically in JSON format.

    Parameters
    ----------
    data : :class:`dict`
        The JSON-like data to be encapsulated within the result.

    Attributes
    ----------
    value : :class:`dict`
        The data associated with the result, stored as a dictionary (JSON-like structure).
    """

    def __init__(self, data: dict):
        """
        Initializes the BasicResult instance with the provided data.
        """
        self.value = data
        self.df = pd.DataFrame(data).rename(
            columns = column_mapping
        )

    def __get__(self):
        """
        Retrieves the stored value.

        Returns
        -------
        dict
            The JSON-like data encapsulated within the instance.
        """
        return self.value
    
    def __str__(self):
        """
        Returns a string representation of the stored data as a DataFrame.

        Returns
        -------
        str
            A string representation of the data in tabular format (Pandas DataFrame).
        """
        return self.df.__str__()


# class BronzeResult(BasicResult):
#     """
#     Encapsulates bronze level data, typically raw data.

#     Parameters
#     ----------
#     data : :class:`dict`
#         The raw data to be encapsulated within the result.
#     """

#     def __init__(self, data: dict):
#         """
#         Initializes the BronzeResult instance with the provided data.
#         """
#         super().__init__(data)


# class SilverResult(BasicResult):
#     """
#     Encapsulates silver level data, typically cleaned data.

#     Parameters
#     ----------
#     data : :class:`dict`
#         The cleaned data to be encapsulated within the result.
#     """

#     def __init__(self, data: dict):
#         """
#         Initializes the SilverResult instance with the provided data.
#         """
#         super().__init__(data)


# class GoldResult(BasicResult):
#     """
#     Encapsulates gold level data, typically aggregated data.

#     Parameters
#     ----------
#     data : :class:`dict`
#         The aggregated data to be encapsulated within the result.
#     """

#     def __init__(self, data: dict):
#         """
#         Initializes the GoldResult instance with the provided data.
#         """
#         super().__init__(data)





class Table:
    def __init__(self, table_name, data_lake = None):
        self.data_lake = data_lake
        self.table_name = table_name
        self.table = None
        self.callback = None
        self.df = None
    
    def generate_table(self):
        if self.callback:
            self.df = self.callback(self)
            self.data_lake.update_metadata(
                table_name = self.table_name,
                level = None,
                created_at = datetime.now(),
                generated = True
            )
        return self.df

class BronzeTable(Table):
    def __init__(self, table_name, data, parsed_data, data_lake = None):
        super().__init__(table_name, data_lake)
        self.raw = data
        self.df = pd.DataFrame(parsed_data).rename(
            columns = column_mapping
        )
        if "timestamp" in self.df.columns:
            self.df.timestamp = pd.to_timedelta(self.df.timestamp)

class SilverTable(Table):
    def __init__(self, table_name, sources, source_tables = {"bronze": [], "silver": [], "gold": []}, data_lake = None):
        super().__init__(table_name, data_lake)
        self.sources = sources
        self.source_tables = source_tables
        self.df = None
        self.dependency_tables = []

    def refine_sources(self):
        for source in self.sources:
            level = self.data_lake._identify_table_level(source)
            if level:
                self.source_tables[level].append(source)
                if level in ["silver", "gold"]:
                    dependency_table = self.data_lake.get(level = level, table_name = source)
                    if dependency_table:
                        self.dependency_tables.append(dependency_table)
                    else:
                        raise ValueError(f"Source table '{source}' not found in data lake.")
            else:
                raise ValueError(f"Source table '{source}' not found in data lake.")

class GoldTable(Table):
    def __init__(self, table_name, sources, source_tables = {"bronze": [], "silver": [], "gold": []}, data_lake = None):
        super().__init__(table_name, data_lake)
        self.sources = sources
        self.source_tables = source_tables
        self.df = None
        self.dependency_tables = []


    def refine_sources(self):
        for source in self.sources:
            level = self.data_lake._identify_table_level(source)
            if level:
                self.source_tables[level].append(source)
                if level in ["silver", "gold"]:
                    dependency_table = self.data_lake.get(level = level, table_name = source)
                    if dependency_table:
                        self.dependency_tables.append(dependency_table)
                    else:
                        raise ValueError(f"Source table '{source}' not found in data lake.")
            else:
                raise ValueError(f"Source table '{source}' not found in data lake.")