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
from ..utils.constants import TOPICS_MAP, SILVER_SESSION_TABLES, TABLE_GENERATION_FUNCTIONS
from ..data_processing.lakes import DataLake
from .driver import Driver

from multiprocessing import Pool
from functools import partial
import multiprocessing
from itertools import repeat


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
        # Silver Data
        for attr in SILVER_SESSION_TABLES:
            setattr(self, attr, None)

        # Iterate over the kwargs and set them as attributes of the instance
        for key, value in locals().items():
            if value: 
                setattr(self, key.lower(), value)  # Set instance attributes based on provided parameters.

        # Build the full path for accessing session data if path attribute exists.
        if hasattr(self, "path"):
            self.full_path = helper.build_session_endpoint(self.path)
    
    def load_session_data(self):
        """
        Load the session data.

        This method loads the session data by fetching the topic names and drivers.
        """
        self.get_topic_names()
        self._load_drivers()

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
            self.topic_names_info[topic]["default_is_stream"] = TOPICS_MAP[topic]["default_is_stream"]

        return self.topic_names_info

    def print_topic_names(self):
        """livetimingF1_getdata(
        urljoin(session.full_path, session.topic_names_info[dataName][dataType]),
        stream=stream
    )

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

    def _load_drivers(self):
        """
        Load the driver list for the session.
        """
        logger.info(f"Fetching drivers.")
        self.drivers = {}
        data = livetimingF1_getdata(
            urljoin(self.full_path, self.topic_names_info["DriverList"]["KeyFramePath"]),
            stream=False
        )
        for key, driver_info in data.items():
            driver = Driver(session=self, **driver_info)
            self.drivers[driver.RacingNumber] = driver


    def get_driver(self, driver_number: str) -> Driver:
        """
        Get a specific driver by their number.

        Parameters
        ----------
        driver_number : str
            The driver's racing number

        Returns
        -------
        Driver
            The Driver object for the specified number
        """
        return self.drivers.get(str(driver_number))

    def load_data(
        self,
        dataNames,
        parallel: bool = False,
        dataType: str = "StreamPath",
    ):
        """
        Retrieve and parse data from feeds, either sequentially or in parallel.

        Parameters
        ----------
        dataNames : Union[str, List[str]]
            Single data name or list of data names to retrieve
        parallel : bool, optional
            Whether to load data in parallel (True) or sequentially (False), by default True
        dataType : str, optional
            The type of the data to fetch, by default "StreamPath"
        stream : bool, optional
            Whether to fetch as stream, by default True

        Returns
        -------
        Union[BasicResult, dict]
            If single data name provided: BasicResult object with parsed data
            If multiple data names: Dictionary mapping names to BasicResult objects

        Notes
        -----
        - For parallel loading, uses multiprocessing Pool with (CPU count - 1) processes
        - Saves all loaded data to bronze lake before returning
        - Returns same format as input: single result for str input, dict for list input
        """
        # Ensure topic names are loaded
        if not hasattr(self, "topic_names_info"):
            self.get_topic_names()

        # Handle single data name case
        single_input = len(dataNames) == 1
        # if single_input:
        #     dataNames = [dataNames]

        # # Validate all data names
        # validated_names = []
        # for name in dataNames:
        #     for topic in self.topic_names_info:
        #         if self.topic_names_info[topic]["key"] == name:
        #             name = topic
        #             stream = self.topic_names_info[topic]["default_is_stream"]
        #             break
        #     validated_names.append((name, stream))

        validated_names = dataNames

        results = {}
        if parallel and len(validated_names) > 1:
            # Parallel loading
            n_processes = max(1, multiprocessing.cpu_count() - 1)
            with Pool(processes=n_processes) as pool:
                loaded_results = pool.starmap(
                    load_single_data, 
                    zip(
                        np.asarray(validated_names)[:,0],
                        repeat(self),
                        np.asarray(validated_names)[:,1]))
                results = {name: result for name, result in loaded_results}
        else:
            # Sequential loading
            for name, stream in validated_names:
                name, res = load_single_data(name, self, stream)
                # logger.info(f"Fetching data : '{name}'")
                # start = time()
                # data = livetimingF1_getdata(
                #     urljoin(self.full_path, self.topic_names_info[name][dataType]),
                #     stream=stream
                # )
                # logger.debug(f"Fetched in {round(time() - start,3)} seconds")
                
                # start = time()
                # res = BasicResult(
                #     data=list(self.etl_parser.unified_parse(name, data))
                # )
                # logger.debug(f"Parsed in {round(time() - start,3)} seconds")
                # logger.info(f"'{name}' has been fetched and parsed")
                results[name] = res

        # Save all results to bronze lake
        for name, result in results.items():
            self.data_lake.put(
                level="bronze", data_name=name, data=result
            )
            logger.debug(f"'{name}' has been saved to the bronze lake.")

        # Return single result or dict based on input type
        if single_input:
            return self.data_lake.get(level="bronze", data_name=validated_names[0][0])
        return {name: self.data_lake.get(level="bronze", data_name=name) 
               for name, stream in validated_names}

    def get_data(
        self,
        dataNames,
        parallel: bool = False,
        force: bool = False
    ):
        """
        Retrieve one or multiple data topics from cache or load them, with optional parallel processing.

        Parameters
        ----------
        data_names : Union[str, List[str]]
            Single data topic name or list of data topic names to retrieve
        parallel : bool, optional
            Whether to use parallel processing when fetching multiple topics.
            Defaults to False.
        force : bool, optional
            Whether to force download data even if it exists in cache.
            Defaults to False.

        Returns
        -------
        Union[BasicResult, Dict[str, BasicResult]]
            If a single topic is requested, returns its BasicResult object.
            If multiple topics are requested, returns a dictionary mapping 
            topic names to their BasicResult objects.

        Examples
        --------
        # Get single topic
        >>> telemetry = session.get_data("CarData.z")
        
        # Get multiple topics in parallel (default)
        >>> data = session.get_data(["CarData.z", "Position.z", "SessionStatus"])
        
        # Get multiple topics sequentially
        >>> data = session.get_data(["CarData.z", "Position.z"], parallel=False)
        
        # Force download data even if cached
        >>> data = session.get_data("CarData.z", force=True)

        Notes
        -----
        - Automatically handles both single and multiple data requests
        - Checks cache (data lake) before loading new data unless force=True
        - Uses parallel processing for multiple topics when parallel=True
        - Returns same format as input: single result for str input, dict for list input
        """
        # Ensure topic names are loaded
        if not hasattr(self, "topic_names_info"):
            self.get_topic_names()
        
        # Handle single data name case
        single_input = isinstance(dataNames, str)
        dataNames = [dataNames] if single_input else dataNames
        
        # Validate all data names
        validated_names = [self.check_data_name(name) for name in dataNames]
        
        # Check cache and identify topics to load
        to_load = []
        results = {}
        
        for name in validated_names:
            if not force and name in self.data_lake.raw:
                logger.debug(f"'{name}' found in lake, using cached version")
                results[name] = self.data_lake.get(level="bronze", data_name=name)
            else:
                stream = self.topic_names_info[name]["default_is_stream"]
                to_load.append((name, stream))
        
        if to_load:
            # Load new data using load_data with parallel option
            loaded_results = self.load_data(
                dataNames=to_load,
                parallel=parallel and len(to_load) > 1
            )
            
            if isinstance(loaded_results, dict):
                results.update(loaded_results)
            else:
                # Handle single result case
                results[to_load[0][0]] = loaded_results
        
        # Return single result if single input, otherwise return dictionary
        return results[validated_names[0]] if single_input else results

    def check_data_name(self, dataName: str):
        """
        Validate and return the correct data name.

        This method checks if the provided data name exists in the `topic_names_info` attribute. 
        If it does, it returns the corresponding topic name.

        Parameters
        ----------
        dataName : :class:`str`
            The name of the data topic to validate.

        Returns
        -------
        :class:`str`
            The validated data name.

        Notes
        -----
        - The method ensures that the provided data name exists in the `topic_names_info` attribute.
        - If the data name is found, it returns the corresponding topic name.
        """
        if not hasattr(self,"topic_names_info"):
            self.get_topic_names()

        for topic in self.topic_names_info:
            if self.topic_names_info[topic]["key"] == dataName:
                dataName = topic
                break

        return dataName

    def get_laps(self):
        """
        Retrieve the laps data.

        This method returns the laps data if it has been generated. If not, it logs an 
        informational message indicating that the laps table is not generated yet.

        Returns
        -------
        :class:`~Laps` or None
            The laps data if available, otherwise None.

        Notes
        -----
        - The method checks if the `laps` attribute is populated.
        - If the `laps` attribute is not populated, it logs an informational message.
        """
        if self.laps is not None:
            return self.laps
        else:
            logger.info("Laps table is not generated yet. Use .generate() to load required data and generate silver tables.")
            return None

    def get_car_telemetry(self):
        """
        Retrieve the car telemetry data.

        This method returns the car telemetry data if it has been generated. If not, it logs an 
        informational message indicating that the car telemetry table is not generated yet.

        Returns
        -------
        :class:`~CarTelemetry` or None
            The car telemetry data if available, otherwise None.

        Notes
        -----
        - The method checks if the `carTelemetry` attribute is populated.
        - If the `carTelemetry` attribute is not populated, it logs an informational message.
        """
        if self.carTelemetry is not None:
            return self.carTelemetry
        else:
            logger.info("Car Telemetry table is not generated yet. Use .generate() to load required data and generate silver tables.")
            return None

    def get_weather(self):
        """
        Retrieve the weather data.

        This method returns the weather data if it has been generated. If not, it logs an 
        informational message indicating that the weather table is not generated yet.

        Returns
        -------
        :class:`~Weather` or None
            The weather data if available, otherwise None.

        Notes
        -----
        - The method checks if the `weather` attribute is populated.
        - If the `weather` attribute is not populated, it logs an informational message.
        """

        logger.error(".get_weather() is not implemented yet.")

        # if self.weather != None: return self.weather
        # else:
        #     logger.info("Weather table is not generated yet. Use .generate() to load required data and generate silver tables.")
        #     return None
    
    def get_timing(self):
        """
        Retrieve the timing data.

        This method returns the timing data if it has been generated. If not, it logs an 
        informational message indicating that the timing table is not generated yet.

        Returns
        -------
        :class:`~Timing` or None
            The timing data if available, otherwise None.

        Notes
        -----
        - The method checks if the `timing` attribute is populated.
        - If the `timing` attribute is not populated, it logs an informational message.
        """

        logger.error(".get_timing() is not implemented yet.")

        # if self.timing != None: return self.timing
        # else:
        #     logger.info("Timing table is not generated yet. Use .generate() to load required data and generate silver tables.")
        #     return None
    
    def _get_first_datetime(self):
        pos_df = self.get_data("Position.z")
        car_df = self.get_data("CarData.z")
        first_date = np.amax([(helper.to_datetime(car_df["Utc"]) - pd.to_timedelta(car_df["timestamp"])).max(), (helper.to_datetime(pos_df["Utc"]) - pd.to_timedelta(pos_df["timestamp"])).max()])
        
        # sess_data = self.get_data("Session_Data")
        # first_date = helper.to_datetime(sess_data[sess_data["SessionStatus"] == "Started"].Utc).tolist()[0]
        return first_date
    
    def _get_session_start_datetime(self):
        # return pd.to_timedelta(self.get_data(dataNames="SessionStatus").set_index("status").loc["Started"].timestamp[0])
        sess_data = self.get_data("Session_Data")
        first_date = helper.to_datetime(sess_data[sess_data["SessionStatus"] == "Started"].Utc).tolist()[0]
        return first_date

    def generate(self, silver=True, gold=False):
        required_data = set(["CarData.z", "Position.z", "SessionStatus"])
        tables_to_generate = set()
        if silver:
            tables_to_generate.update(SILVER_SESSION_TABLES)
        if gold:
            tables_to_generate.update(GOLD_SESSION_TABLES)
        for table_name in tables_to_generate:
            required_data.update(TABLE_REQUIREMENTS[table_name])
        
        # Use the unified get_data method instead of get_data_parallel
        self.get_data(list(required_data), parallel=True)

        self.first_datetime = self._get_first_datetime()
        # self.session_start_time = self._get_session_start_time()
        self.session_start_datetime = self._get_session_start_datetime()
        
        if silver:
            logger.info(f"Silver tables are being generated.")
            for table_name in SILVER_SESSION_TABLES:
                if table_name in TABLE_GENERATION_FUNCTIONS:
                    setattr(self, table_name, self.data_lake.silver_lake.generate_table(table_name))
                    logger.info(f"'{table_name}' has been generated and saved to the silver lake. You can access it from 'session.{table_name}'.")
        
        if gold:
            logger.info("Gold tables are not implemented yet.")
            pass
    
    def generate_laps_table(self):
        setattr(self, "laps", self.data_lake.silver_lake.generate_table("laps"))
    
    def generate_car_telemetry_table(self):
        setattr(self, "car_telemetry", self.data_lake.silver_lake.generate_table("laps"))


def load_single_data(dataName, session, stream):

    if stream: dataType = "StreamPath"
    else: dataType = "KeyFramePath"

    logger.info(f"Fetching data : '{dataName}'")
    start = time()
    data = livetimingF1_getdata(
        urljoin(session.full_path, session.topic_names_info[dataName][dataType]),
        stream=stream
    )
    logger.debug(f"Fetched in {round(time() - start,3)} seconds")
    # Parse the retrieved data using the ETL parser and return the result.
    start = time()
    res = BasicResult(
        data=list(session.etl_parser.unified_parse(dataName, data))
    )
    logger.debug(f"Parsed in {round(time() - start,3)} seconds")
    logger.info(f"'{dataName}' has been fetched and parsed")

    # session.data_lake.put(
    #     level="bronze", data_name=dataName, data=res
    # )
    # logger.debug(f"'{dataName}' has been saved to the bronze lake.")

    return dataName, res


# session.load()
# session.generate(silver=True, gold=False)

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