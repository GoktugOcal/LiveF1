# Standard Library Imports
from urllib.parse import urljoin
from typing import List, Dict
from time import time
import functools

# Third-Party Library Imports
# (No third-party libraries imported in this file)

# Internal Project Imports
from ..adapters import livetimingF1_request, livetimingF1_getdata
from ..utils import helper
from ..utils.logger import logger
from ..data_processing.etl import *
from ..data_processing.data_models import *
from ..data_processing.silver_functions import *
from ..utils.constants import TOPICS_MAP, SILVER_SESSION_TABLES, TABLE_GENERATION_FUNCTIONS
from ..utils.exceptions import *
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

    def _load_default_silver_tables(self):
        for table_name in SILVER_SESSION_TABLES:
            self.create_silver_table(table_name, TABLE_REQUIREMENTS[table_name], include_session=True)(globals()[TABLE_GENERATION_FUNCTIONS[table_name]])
    

    def _load_circuit_data(self):
        circuit = self.meeting.circuit
        circuit._load_circuit_data()
        self.data_lake.create_bronze_table(table_name="track_regions", raw_data=circuit._raw_circuit_data, parsed_data=circuit.track_regions)

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


    def get_driver(self, identifier: str) -> Driver:
        """
        Get a specific driver by their number, name, or short name.

        Parameters
        ----------
        identifier : str
            The driver's racing number, full name, or short name.

        Returns
        -------
        Driver
            The Driver object for the specified identifier, or None if not found.
        """
        for driver in self.drivers.values():
            if (
                str(driver.RacingNumber) == identifier or
                driver.FirstName.lower() == identifier.lower() or
                driver.LastName.lower() == identifier.lower() or
                driver.Tla.lower() == identifier.lower()
            ):
                return driver
        return None

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
        validated_names = dataNames

        results = {}
        if parallel and len(validated_names) > 1:
            # Parallel loading
            n_processes = max(1, multiprocessing.cpu_count() - 1)
            print(validated_names)
            with Pool(processes=n_processes) as pool:
                loaded_results = pool.starmap(
                    load_single_data, 
                    zip(
                        np.asarray(validated_names)[:,0],
                        repeat(self),
                        np.asarray(validated_names)[:,1]))
                results = {name: {"data": data, "parsed_data": parsed_data} for name, data, parsed_data in loaded_results}
        else:
            # Sequential loading
            for name, stream in validated_names:
                name, data, parsed_data = load_single_data(name, self, stream)
                results[name] = {"data": data, "parsed_data": parsed_data}

        # Save all results to bronze lake
        for name, result in results.items():
            self.data_lake.create_bronze_table(table_name=name, raw_data=result["data"], parsed_data=result["parsed_data"])
            logger.debug(f"'{name}' has been saved to the bronze lake.")

        # Return single result or dict based on input type
        if single_input:
            return self.data_lake.get(level="bronze", table_name=validated_names[0][0])
        return {name: self.data_lake.get(level="bronze", table_name=name)
               for name, stream in validated_names}

    def get_table(
        self,
        dataNames,
        level = "bronze",
        parallel: bool = False,
        force: bool = False
    ):
        if isinstance(dataNames, str):
            return self.get(
                dataNames,
                level=level,
                parallel= parallel,
                force = force)

        elif isinstance(dataNames, list):
            res = self.get(
                dataNames,
                level=level,
                parallel= parallel,
                force = force
                )
            return {name:table for name, table in res.items()}
        else: return None

    def get_data(
        self,
        dataNames,
        level = "bronze",
        parallel: bool = False,
        force: bool = False
    ):
        if isinstance(dataNames, str):
            return self.get(
                dataNames,
                level=level,
                parallel= parallel,
                force = force).df

        elif isinstance(dataNames, list):
            res = self.get(
                dataNames,
                level=level,
                parallel= parallel,
                force = force
                )
            return {name:table.df for name, table in res.items()}
        else: return None

    def get(
        self,
        dataNames,
        level = "bronze",
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

        if level == "bronze":
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
                if not force and name in self.data_lake.metadata:
                    logger.debug(f"'{name}' found in lake, using cached version")
                    results[name] = self.data_lake.get(level="bronze", table_name=name)
                else:
                    logger.debug(f"'{name}' not found in lake, loading from livetiming.")
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
        
        else:
            # Handle single data name case
            single_input = isinstance(dataNames, str)
            dataNames = [dataNames] if single_input else dataNames

            results = {}
            for name in dataNames:
                if name in self.data_lake.metadata:
                    if self.data_lake.metadata[name]["generated"]:
                        logger.debug(f"'{name}' has been created and generated.")
                        results[name] = self.data_lake.get(level=level, table_name=name)
                    else:
                        logger.debug(f"'{name}' has been created but not generated yet. It is being generated...")
                        self.data_lake.get(level=level, table_name=name).generate_table()
                        results[name] = self.data_lake.get(level=level, table_name=name)
            
            return results[dataNames[0]] if single_input else results

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
            if (self.topic_names_info[topic]["key"].lower() == dataName.lower()) or (topic.lower() == dataName.lower()):
                dataName = topic
                return dataName
        
        return dataName

        # raise TopicNotFoundError(f"The topic name you provided '{dataName}' is not included in the topics.")
    
    # def normalize_topic_name(self, topicName):
    #     """
    #     Normalize the topic name.
    #     """

    #     if not hasattr(self,"topic_names_info"):
    #         self.get_topic_names()

    #     for topic in self.topic_names_info:
    #         if (self.topic_names_info[topic]["key"].lower() == topicName.lower()) or (topic.lower() == topicName.lower()):
    #             topicName = topic
    #             break

    #     return topicName

    def _identify_data_level(self, dataName):

        corrected_data_name = self.check_data_name(dataName)
        if corrected_data_name: return "bronze"
        else:
            for table_name, info in self.data_lake.metadata.items():
                if dataName == table_name: return info["table_type"]
        
        return None

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

    # def get_weather(self):
    #     """
    #     Retrieve the weather data.

    #     This method returns the weather data if it has been generated. If not, it logs an 
    #     informational message indicating that the weather table is not generated yet.

    #     Returns
    #     -------
    #     :class:`~Weather` or None
    #         The weather data if available, otherwise None.

    #     Notes
    #     -----
    #     - The method checks if the `weather` attribute is populated.
    #     - If the `weather` attribute is not populated, it logs an informational message.
    #     """

    #     logger.error(".get_weather() is not implemented yet.")
    
    # def get_timing(self):
    #     """
    #     Retrieve the timing data.

    #     This method returns the timing data if it has been generated. If not, it logs an 
    #     informational message indicating that the timing table is not generated yet.

    #     Returns
    #     -------
    #     :class:`~Timing` or None
    #         The timing data if available, otherwise None.

    #     Notes
    #     -----
    #     - The method checks if the `timing` attribute is populated.
    #     - If the `timing` attribute is not populated, it logs an informational message.
    #     """

    #     logger.error(".get_timing() is not implemented yet.")
    
    def _get_first_datetime(self):
        pos_df = self.get_data("Position.z")
        car_df = self.get_data("CarData.z")
        first_date = np.amax(
            [
                (helper.to_datetime(car_df["Utc"]) - pd.to_timedelta(car_df["timestamp"])).max(),
                (helper.to_datetime(pos_df["Utc"]) - pd.to_timedelta(pos_df["timestamp"])).max()
            ]
        )
        return first_date
    
    def _get_session_start_datetime(self):
        # return pd.to_timedelta(self.get_data(dataNames="SessionStatus").set_index("status").loc["Started"].timestamp[0])
        sess_data = self.get_data("Session_Data")
        first_date = helper.to_datetime(sess_data[sess_data["SessionStatus"] == "Started"].Utc).tolist()[0]
        return first_date

    def generate(self, silver=True, gold=False):
        
        self._load_circuit_data()

        required_data = set(["CarData.z", "Position.z", "SessionStatus"])
        tables_to_generate = set()
        if silver:
            self._load_default_silver_tables()
            silver_tables_to_generate = [self.data_lake.get("silver", table_name) for table_name, info in self.data_lake.metadata.items() if info["table_type"] == "silver"]
            tables_to_generate.update(silver_tables_to_generate)
            # refine sources for each silver table
            for silver_table in silver_tables_to_generate:
                silver_table.refine_sources()
                required_data.update(set(silver_table.source_tables["bronze"]))
        
        if gold:
            gold_tables_to_generate = [self.data_lake.get("gold", table_name) for table_name, info in self.data_lake.metadata.items() if info["table_type"] == "gold"]
            tables_to_generate.update(gold_tables_to_generate)
            # refine sources for each gold table
            for gold_table in gold_tables_to_generate:
                gold_table.refine_sources()
                required_data.update(set(gold_table.source_tables["bronze"]))

        # Use the unified get_data method instead of get_data_parallel
        logger.info(f"Topics to be loaded : {list(required_data)}")
        self.get_data(list(required_data), parallel=False)

        self.first_datetime = self._get_first_datetime()
        self.session_start_datetime = self._get_session_start_datetime()

        if self.data_lake._check_circular_dependencies():
            if silver:
                logger.info(f"Silver tables are being generated.")
                for silver_table in silver_tables_to_generate:
                    table_name = silver_table.table_name
                    silver_table.generate_table()
                    setattr(self, table_name, self.get_data(dataNames = table_name, level = "silver"))
                    logger.info(f"'{table_name}' has been generated and saved to the silver lake. You can access it from 'session.{table_name}'.")
            
            if gold:
                logger.info("Gold tables are being generated.")
                for gold_table in gold_tables_to_generate:
                    table_name = gold_table.table_name
                    gold_table.generate_table()
                    setattr(self, table_name, self.get_data(dataNames = table_name, level = "gold"))
                    logger.info(f"'{table_name}' has been generated and saved to the gold lake. You can access it from 'session.{table_name}'.")
        else:
            logger.error("Circular dependencies detected. Please check your table dependencies.")


    def _create_table(self, level, table_name, source_tables, include_session=False):
        """
        Decorator factory that creates a SilverTable instance
        
        Args:
            table_name: Name for the silver table
            source_tables: List of source table names to use from bronze lake
        
        Returns:
            Decorator function that will register the callback for table generation
        """
        import inspect

        if include_session:
            param_table = ["_session"] + source_tables
        
       
        if level == "silver":
            source_dict = {
                "bronze" : [],
                "silver" : [],
                "unknown" : []
            }

        elif level == "gold":
            source_dict = {
                "bronze" : [],
                "silver" : [],
                "gold" : [],
                "unknown" : []
            }
        
        def decorator(callback_func):

            # Inspect the function signature to get parameter names
            sig = inspect.signature(callback_func)
            param_names = list(sig.parameters.keys())
            
            # Create mapping from source tables to parameter names
            if len(param_names) != len(param_table):
                raise ValueError(f"Function {callback_func.__name__} has {len(param_names)} parameters, but {len(param_table)} source tables were specified.\nRequired parameters: {param_table}")
            param_mapping = dict(zip(param_table, param_names))

            # # Check if the table is a topic name and if it is, add it to the source_dict
            # for table, param_name in param_mapping.items():
            #     if table == "_session": continue
            #     else:
            #         table_level = self._identify_data_level(table)
            #         print(table, "-", table_level)
            #         if table_level: source_dict[table_level].append(table)
            #         else:
            #             # source_dict["unknown"].append(table)
            #             # logger.info(f"The table name you provided '{table}' is not loaded yet, it is expected to be loaded in the future. PLEASE MAKE SURE IT IS GOING TO BE CREATED.")
            #             raise TopicNotFoundError(f"The table name you provided '{table}' is not a topic name.\nIf it is a table name from another level, SOURCE TABLES FROM ANOTHER LEVELS ARE NOT SUPPORTED YET.\nPlease call the table by `session.get_data('{table}')` inside the callback you are decorating.")

            # source_objs = [] # TODO: Add sources from different levels

            @functools.wraps(callback_func)
            def wrapped_callback(*args, **kwargs):
                # Get the source tables from bronze lake
                source_data = {}
                for table, param_name in param_mapping.items():
                    if table == "_session": 
                        source_data[param_name] = self
                    else:
                        # TODO: Add sources from different levels
                        table_level = self.data_lake._identify_table_level(table)
                        # source_dict[table_level].append(table)
                        if table_level == None: raise TopicNotFoundError(f"The topic name you provided '{table}' is not included in any level.")
                        elif table_level == "bronze":
                            topic_name = self.check_data_name(table)
                        else: topic_name = table

                        # table_level = "bronze"
                        # topic_name = self.check_data_name(table)

                        temp_table = self.get_table(topic_name, level=table_level)
                        source_data[param_name] = temp_table.df
                        # source_objs.append(temp_table) # TODO: Add sources from different levels

                # Call the original function with source data as parameters
                result = callback_func(**source_data)
                return result
            
            # if include_session:
            #     source_dict["bronze"].append("_session")

            if level == "silver":
                # Create a new SilverTable instance
                new_table = SilverTable(table_name=table_name, sources=source_tables)
                new_table.callback = wrapped_callback
            
            elif level == "gold":
                # Create a new SilverTable instance
                new_table = GoldTable(table_name=table_name, sources=source_tables)
                new_table.callback = wrapped_callback

            # Store the table in the selected lake
            self.data_lake.put(level=level, table_name=table_name, table=new_table)
            
            # Return the original function for documentation purposes
            return callback_func
        
        logger.info(f"The callback function for the SILVER table '{table_name}' was set.")

        return decorator

    def create_silver_table(self, table_name, source_tables, include_session=False):

        return self._create_table(
            level = "silver",
            table_name = table_name,
            source_tables = source_tables,
            include_session = include_session
            )
        
    def create_gold_table(self, table_name, source_tables, include_session=False):
        
        return self._create_table(
            level = "gold",
            table_name = table_name,
            source_tables = source_tables,
            include_session = include_session
            )

def load_single_data(dataName, session, stream):

    if stream: dataType = "StreamPath"
    else: dataType = "KeyFramePath"

    logger.debug(f"Fetching data : '{dataName}'")
    start = time()
    data = livetimingF1_getdata(
        urljoin(session.full_path, session.topic_names_info[dataName][dataType]),
        stream=stream
    )
    logger.debug(f"Fetched in {round(time() - start,3)} seconds")
    # Parse the retrieved data using the ETL parser and return the result.
    start = time()
    parsed_data = list(session.etl_parser.unified_parse(dataName, data))

    logger.debug(f"Parsed in {round(time() - start,3)} seconds")
    logger.info(f"'{dataName}' has been fetched and parsed")

    return dataName, data, parsed_data