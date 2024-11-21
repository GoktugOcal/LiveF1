# Standard Library Imports
import json

# Third-Party Library Imports
import pandas as pd


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
        return pd.DataFrame(self.value).__str__()
