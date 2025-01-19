# Standard Library Imports
from urllib.parse import urljoin
from typing import List, Dict
from time import time

# Third-Party Library Imports
# (No third-party libraries imported in this file)

# Internal Project Imports
from ..adapters import livetimingF1_request, livetimingF1_getdata
from ..utils import helper
from ..utils.logger import logger
from ..data_processing.etl import *
from ..data_processing.data_models import *
from ..utils.constants import TOPICS_MAP
from ..data_processing.lakes import DataLake


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
        self.data_lake = DataLake(self)
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
        Retrieve information about available data topics for the session.

        This method fetches details about the available data topics for the session 
        from the live timing feed and enriches the data with descriptions and keys 
        from a predefined `TOPICS_MAP`.

        Returns
        -------
        :class:`dict`
            A dictionary containing information about available data topics. Each key 
            represents a topic, and its value is another dictionary with the following keys:
            - `description` (str): A description of the topic.
            - `key` (str): A unique key identifying the topic.
            - Other metadata provided by the live timing feed.

        Notes
        -----
        - The data is fetched from a URL formed by appending `"Index.json"` to the session's 
        `full_path`.
        - The fetched data is enriched with additional information from the `TOPICS_MAP` 
        dictionary.
        - The `topic_names_info` attribute is set to the resulting dictionary for later use.

        Examples
        -------------
        The returned dictionary would be:

        .. code-block:: json

            {
                "Topic1": {
                    "KeyFramePath": "Topic1.json",
                    "StreamPath": "Topic1.jsonStream"
                    "description": "Description for Topic1",
                    "key": "T1"
                },
                "Topic2": {
                    "KeyFramePath": "Topic2.json",
                    "StreamPath": "Topic2.jsonStream"
                    "description": "Description for Topic2",
                    "key": "T2"
                }
            }

        """
        logger.debug(f"Getting topic names for the session: {self.meeting.name}: {self.name}")
        self.topic_names_info = livetimingF1_request(urljoin(self.full_path, "Index.json"))["Feeds"]
        for topic in self.topic_names_info:
            self.topic_names_info[topic]["description"] = TOPICS_MAP[topic]["description"]
            self.topic_names_info[topic]["key"] = TOPICS_MAP[topic]["key"]

        return self.topic_names_info

    def print_topic_names(self):
        """
        Print the topic names and their descriptions.

        This method prints the key and description for each topic available in 
        the `topic_names_info` attribute. If the `topic_names_info` attribute is not 
        already populated, it fetches the data using the `get_topic_names` method.

        Notes
        -----
        - The method assumes the `topic_names_info` attribute is a dictionary 
        where each key represents a topic, and its value is another dictionary
        containing `key` and `description`.
        - The `get_topic_names` method is called if `topic_names_info` is not 
        already populated.

        Examples
        -------------
        The output would be:

        .. code-block:: plain

            T1 : 
                Description for topic 1
            T2 : 
                Description for topic 2

        """
        if not hasattr(self, "topic_names_info"):
            self.get_topic_names()

        
        logger.debug(f"Printing topic names and descriptions for the session: {self.meeting.name}: {self.name}")
        for topic in self.topic_names_info:
            print(self.topic_names_info[topic]["key"], ": \n\t", self.topic_names_info[topic]["description"])

    def load_data(
        self,
        dataName,
        dataType : str = "StreamPath",
        stream : bool = True
        ):
        """
        Retrieve and parse data from a specific feed.

        This method fetches data from a live timing feed based on the provided data name and 
        type, processes it using the ETL parser, and returns the results.

        Parameters
        ----------
        dataName : :class:`str`
            The name of the data topic to retrieve, as specified in `topic_names_info`.
        dataType : :class:`str`
            The type of the data to fetch. This is used to determine the feed path. 
            Currently overridden to `"StreamPath"` within the method.
        stream : :class:`bool`
            Whether to fetch the data as a stream. This is currently overridden to `True` 
            within the method.

        Returns
        -------
        :class:`~BasicResult`
            An object containing the parsed data as a list of results.

        Notes
        -----
        - The `dataType` and `stream` parameters are hardcoded to `"StreamPath"` and `True` 
        respectively within the method, making their input values unused.
        - The feed URL is constructed using the session's `full_path` and the `StreamPath` 
        for the specified `dataName` from `topic_names_info`.
        - The retrieved data is processed through the ETL parser's `unified_parse` method 
        before being wrapped into a `BasicResult` object.

        Examples
        ----------
        
        Calling the method as:

        .. code-block:: python

            result = self.get_data(dataName="Car_Data")
        
        will:

        1. Fetch the data from the URL: `<full_path>/CarData.z.jsonStream`.

        2. Parse the data using `unified_parse` with `dataName = "CarData.z"`.

        3. Return a `BasicResult` object containing the parsed data.

        Raises
        ------
        KeyError
            If the specified `dataName` does not exist in `topic_names_info`.

        """
        
        dataType = "StreamPath"
        stream = True
        
        if not hasattr(self,"topic_names_info"):
            self.get_topic_names()

        for topic in self.topic_names_info:
            if self.topic_names_info[topic]["key"] == dataName:
                dataName = topic
                break
        
        logger.info(f"Getting requested data : '{dataName}'.\n\tSelected session : {self.season.year} {self.meeting.name} {self.name}\n\tTopic : {dataName}")

        start = time()
        data = livetimingF1_getdata(
            urljoin(self.full_path, self.topic_names_info[dataName][dataType]),
            stream=stream
        )
        logger.debug(f"Data has been get in {round(time() - start,3)} seconds")
        logger.info("Data is successfully received.")

        # Parse the retrieved data using the ETL parser and return the result.
        start = time()
        res = BasicResult(
            data=list(self.etl_parser.unified_parse(dataName, data))
        )
        logger.debug(f"Data has been parsed in {round(time() - start,3)} seconds")
        logger.info("Data is successfully parsed.")

        self.data_lake.put(
            data_name=dataName, data=res
            )

        return res

    def get_data(self, dataName: str):
        s = time()
        dataName = self.check_data_name(dataName)
        print(time() - s)

        if dataName in self.data_lake.raw:
            logger.info(f"'{dataName}' has been found in lake.")
            return BasicResult(data=self.data_lake.raw)
        else:
            logger.info(f"'{dataName}' has not been found in lake, loading it.")
            return self.load_data(dataName)

    
    def check_data_name(self, dataName: str):
        if not hasattr(self,"topic_names_info"):
            self.get_topic_names()

        for topic in self.topic_names_info:
            if self.topic_names_info[topic]["key"] == dataName:
                dataName = topic
                break

        return dataName



# session.load(
#     bronze=True,
#     silver=True,
#     gold=True
#     )

# session.telemetry
# session.timing
# session.weather
# session.position

# telemetry
# coordinates
# tyre
# stint
# position

# laps
# pitduration
# pitstops
# timings

# bronzeLake
# silverLake
# goldLake