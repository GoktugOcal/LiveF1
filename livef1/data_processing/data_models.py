# Standard Library Imports
import json

# Third-Party Library Imports
import pandas as pd


class BasicResult:
    """
    A class to encapsulate a basic result dataset.

    Attributes:
        value (json): The data associated with the result, typically in JSON format.
    """

    def __init__(self, data: json):
        """
        Initializes the BasicResult instance with provided data.

        Args:
            data (json): The JSON data to be stored in the result.
        """
        self.value = data

    def __get__(self):
        """
        Retrieves the stored value.

        Returns:
            The stored data.
        """
        return self.value
    
    def __str__(self):
        """
        Returns a string representation of the stored data as a DataFrame.

        Returns:
            str: A string representation of the data in DataFrame format.
        """
        return pd.DataFrame(self.value).__str__()
