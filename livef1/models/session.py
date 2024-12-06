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

    Attributes
    ----------
    season : :class:`~Season`
        The season the session belongs to.
    year : :class:`int`
        The year of the session.
    meeting : :class:`~Meeting`
        The meeting the session is part of.
    key : :class:`int`
        Unique identifier for the session.
    name : :class:`str`
        Name of the session.
    type : :class:`str`
        Type of the session (e.g., practice, qualifying, race).
    number : :class:`int`
        The session number.
    startdate : :class:`str`
        Start date and time of the session.
    enddate : :class:`str`
        End date and time of the session.
    gmtoffset : :class:`str`
        GMT offset for the session's timing.
    path : :class:`dict`
        Path information for accessing session data.
    loaded : :class:`bool`
        Indicates whether the session data has been loaded.
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
        Retrieves information about available data topics for the session.

        Returns
        -------
        dict
            A dictionary containing information about available data topics for the session.
        """
        self.topic_names_info = livetimingF1_request(urljoin(self.full_path, "Index.json"))["Feeds"]
        return self.topic_names_info

    def get_data(self, dataName, dataType, stream):
        """
        Retrieves data from a specific feed based on the provided data name and type.

        Parameters
        ----------
        dataName : :class:`str`
            The name of the data to retrieve.
        dataType : :class:`str`
            The type of the data to retrieve.
        stream : :class:`str`
            The stream to use for fetching the data.

        Returns
        -------
        :class:`BasicResult`
            An object containing the parsed data.
        """
        
        data = livetimingF1_getdata(
            urljoin(self.full_path, self.topic_names_info[dataName][dataType]),
            stream=stream
        )
        
        # Parse the retrieved data using the ETL parser and return the result.
        return BasicResult(
            data=list(self.etl_parser.unified_parse(dataName, data))
        )