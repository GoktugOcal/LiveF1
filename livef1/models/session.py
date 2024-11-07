# Standard Library Imports
from urllib.parse import urljoin
from typing import List, Dict

# Third-Party Library Imports
# (No third-party libraries imported in this file)

# Internal Project Imports
from ..adapters import livetimingF1_request, livetimingF1_getdata
from ..utils import helper
from ..data_processing.etl import *
from ..data_processing.data_models import *


class Session:
    """
    Represents a Formula 1 session, containing methods to retrieve live timing data and process it.
    
    Attributes:
        season (Season): The season the session belongs to.
        meeting (Meeting): The meeting the session is part of.
        year (int): The year of the session.
        key (int): Unique identifier for the session.
        name (str): Name of the session.
        type (str): Type of the session (e.g., practice, qualifying, race).
        number (int): The session number (e.g., 1, 2, 3).
        startdate (str): Start date and time of the session.
        enddate (str): End date and time of the session.
        gmtoffset (str): GMT offset for the session's timing.
        path (Dict): Path information for accessing session data.
        loaded (bool): Indicates whether the session data has been loaded.
        full_path (str): The complete endpoint URL for accessing session data.
        topic_names_info (dict): Information about available data topic_names for the session.
        etl_parser (livef1SessionETL): An ETL parser instance for processing session data.
    """
    
    def __init__(
        self,
        season: "Season" = None,
        year: int = None,
        meeting: "Meeting" = None,
        key: int = None,
        name: str = None,
        type: str = None,
        number: int = None,
        startdate: str = None,
        enddate: str = None,
        gmtoffset: str = None,
        path: Dict = None,
        loaded: bool = False,
        **kwargs
    ):
        """
        Initializes the Session object with the given parameters.

        Args:
            season (Season): The season the session belongs to.
            year (int): The year of the session.
            meeting (Meeting): The meeting the session is part of.
            key (int): Unique identifier for the session.
            name (str): Name of the session.
            type (str): Type of the session.
            number (int): The session number.
            startdate (str): Start date and time of the session.
            enddate (str): End date and time of the session.
            gmtoffset (str): GMT offset for the session's timing.
            path (Dict): Path information for accessing session data.
            loaded (bool): Indicates whether the session data has been loaded.
        """
        self.season = season
        self.loaded = loaded
        self.etl_parser = livef1SessionETL(session=self)  # Create an ETL parser for the session.

        # Iterate over the kwargs and set them as attributes of the instance
        for key, value in locals().items():
            if value: 
                setattr(self, key.lower(), value)  # Set instance attributes based on provided parameters.

        # Build the full path for accessing session data if path attribute exists.
        if hasattr(self, "path"):
            self.full_path = helper.build_session_endpoint(self.path)

    def get_topic_names(self):
        """
        Retrieves information about available data topic_names for the session.

        Returns:
            dict: Information about the topic_names available for the session.
        """
        self.topic_names_info = livetimingF1_request(urljoin(self.full_path, "Index.json"))["Feeds"]
        return self.topic_names_info

    def get_data(self, dataName, dataType, stream):
        """
        Retrieves data from a specific feed based on the provided data name and type.

        Args:
            dataName (str): The name of the data to retrieve.
            dataType (str): The type of the data to retrieve.
            stream (str): The stream to use for fetching the data.

        Returns:
            BasicResult: An object containing the parsed data.
        """
        data = livetimingF1_getdata(
            urljoin(self.full_path, self.topic_names_info[dataName][dataType]),
            stream=stream
        )
        
        # Parse the retrieved data using the ETL parser and return the result.
        return BasicResult(
            data=list(self.etl_parser.unified_parse(dataName, data))
        )
