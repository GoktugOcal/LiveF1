import asyncio
import concurrent
import requests
import inspect
import random

import time
import json
from urllib.parse import urljoin

from ..data_processing.etl import function_map
from .signalr_aio._connection import Connection
from ..utils.logger import logger
from ..utils.constants import (
    DEFAULT_METHOD,
    BASE_URL,
    SIGNALR_ENDPOINT,
    REALTIME_CALLBACK_DEFAULT_PARAMETERS
    )
from ..utils.exceptions import (
    ArgumentError,
    ParsingError
)

class RealF1Client:
    """
    A client for managing real-time Formula 1 data streaming.

    Attributes
    ----------
    topics : list
        List of topics to subscribe to for receiving live data.
    headers : dict
        HTTP headers used for the connection.
    _connection_url : str
        URL for the SignalR connection.
    _log_file_name : str
        Path to the log file.
    _log_file_mode : str
        Mode for opening the log file.
    _test : bool
        Indicates if the client is in test mode.
    _log_file : file object
        Log file object for writing messages (used in test mode).
    _handlers : dict
        Mapping of methods to their respective handlers.

    Parameters
    ----------
    topics : str or list
        Topic(s) to subscribe to for live updates.
    log_file_name : str, optional
        Name of the log file (default is None).
    log_file_mode : str, optional
        Mode for opening the log file (default is "w").

    """
    def __init__(
        self, 
        topics,
        log_file_name = None,
        log_file_mode = "w",
        ):

        self._connection_url = urljoin(BASE_URL, SIGNALR_ENDPOINT)
        self.headers = {
            'User-agent': 'BestHTTP',
            'Accept-Encoding': 'gzip, identity',
            'Connection': 'keep-alive, Upgrade'}

        if isinstance(topics, str): self.topics = [topics]
        elif isinstance(topics, list): self.topics = topics
        else: raise ArgumentError("You need to give list of topics you want to subscribe")
        
        self._log_file_name = log_file_name
        self._log_file_mode = log_file_mode
        self._handlers = {}

        if self._log_file_name:
            self._log_file = open(self._log_file_name, self._log_file_mode)
            @self.callback("default logger")
            async def print_callback(
                records
                ):
                for topic, data in records.items():
                    for record in data:
                        await self._file_logger(f"{topic} > {record}")

    def _create_session(self):
        """
        Create an HTTP session with the required headers.

        Returns
        -------
        requests.Session
            A configured HTTP session.
        """
        session = requests.Session()
        session.headers = self.headers
        return session
    
    async def _on_message(self, msg):
        """
        Handle incoming messages asynchronously.

        Parameters
        ----------
        msg : dict
            The incoming message to process.
        """
        self._t_last_message = time.time()
        loop = asyncio.get_running_loop()
        try:
            with concurrent.futures.ThreadPoolExecutor() as pool:
                await loop.run_in_executor(
                    pool, print, str(msg)
                )
        except Exception as e:
            raise RealF1Error(e)

    async def _file_logger(self, msg):
        """
        Log incoming messages to a file.

        Parameters
        ----------
        msg : dict
            The incoming message to log.
        """

        if msg != {} and msg:
            self._log_file.write(str(msg) + '\n')
            self._log_file.flush()
        
    def on_message(self, method, handler):
        """
        Register a handler for a specific method.

        Parameters
        ----------
        method : str
            The method to handle.
        handler : callable
            The function to handle the method.
        """
        if method not in self._handlers:
            func = MessageHandlerTemplate(handler).get
            self._handlers[method] = func

    def callback(self, method):
        """
        Decorator to register a callback function for a specific method.

        This decorator allows you to associate a callback function with a particular
        method. The function being registered must have arguments matching the 
        required parameters defined in `REALTIME_CALLBACK_DEFAULT_PARAMETERS`.

        Raises
        ------
        TypeError
            If the provided callback function does not have the required arguments.

        Notes
        -----
        - The `REALTIME_CALLBACK_DEFAULT_PARAMETERS` is a predefined list of parameter 
          names that the callback function must include.
        - Once the function is successfully registered, it will handle messages for the
          specified method.

        Examples
        --------
        Registering a callback for a method:

        .. code-block:: python

            from livef1.adapters.realtime_client import RealF1Client

            client = RealF1Client(
                topics = ["CarData.z", "SessionInfo"],
                log_file_name="./output.json"
            )

            @client.callback("new one")
            async def print_callback(records): # records argument have to be set
                print(records) # or you can do whatever you want with incoming data
            
            client.run()

        """
        def inner(func):
            # Check if the provided function has the required arguments
            has_args = set(REALTIME_CALLBACK_DEFAULT_PARAMETERS) == set(inspect.signature(func).parameters.keys())
            args_diff = set(REALTIME_CALLBACK_DEFAULT_PARAMETERS).difference(set(inspect.signature(func).parameters.keys()))
            if not has_args:
                raise ArgumentError(f"The provided callback function does not have following required arguments. {args_diff}")
            else:
                # Register the function as a handler for the given method
                self.on_message(method,func)
                logger.debug(f"Custom callback method with '{method}' has successfully inserted.")
            return func
        return inner

    def run(self):
        """
        Start the client in asynchronous mode.
        """
        start = time.time()
        self._async_engine_run()
        logger.info(f"Client have run for {(time.time() - start):.2f} seconds.")

    def _async_engine_run(self):
        """
        Execute the asynchronous engine.
        """
        try:
            asyncio.run(self._async_run())
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt - exiting...")
    
    async def _async_run(self):
        """
        Run the client asynchronously.
        """
        logger.info(f"Starting LiveF1 live timing client")
        await asyncio.gather(
            asyncio.ensure_future(self._forever_check()),
            asyncio.ensure_future(self._run())
            )
        logger.info("Exiting...")

    async def _forever_check(self):
        """
        Keep the client running indefinitely.
        """
        while True:
            await asyncio.sleep(1)
        
    def _sync_engine_run(self):
        pass
    
    def _sync_engine(self):
        pass
    
    async def _run(self):
        """
        Set up the SignalR connection and register handlers.
        """
        # Create connection
        self._connection = Connection(self._connection_url, session=self._create_session())
        # Register hub
        hub = self._connection.register_hub('Streaming')
        # Set default message handler
        for method, handler in self._handlers.items():
            hub.client.on(method, handler)

        # Subscribe topics in interest
        hub.server.invoke("Subscribe", self.topics)
        # Start the client
        loop = asyncio.get_event_loop()
        executor = concurrent.futures.ThreadPoolExecutor()
        await loop.run_in_executor(executor, self._connection.start)


class MessageHandlerTemplate:
    """
    A template for handling incoming SignalR messages.

    This class serves as a message handler for SignalR streams, where incoming 
    messages are processed and passed to a user-defined function.

    Parameters
    ----------
    func : callable
        A user-defined asynchronous function that processes the parsed records
        from incoming SignalR messages. The function must accept the processed 
        records as its input.
    """
    def __init__(
        self,
        func
    ):
        self._func = func
    
    async def get(self, msg):
        """
        Process incoming messages and invoke the handler function.

         The method handles two types of incoming message formats:
        - Messages in the "R" key: Representing topics with associated data.
        - Messages in the "M" key: Representing method calls with data payloads.

        For each message, the method uses a `function_map` to parse the data and 
        sends the resulting records to the user-defined handler function.

        Parameters
        ----------
        msg : dict
            The incoming message in SignalR format. It is expected to contain either:
            - "R": A dictionary where the keys represent topic names and the values
              are the associated data for that topic.
            - "M": A list of dictionaries, where each dictionary contains:
              - "M": The method name.
              - "A": A list of message components including topic name, data, and timestamp.

        """
        batch = msg

        if ("R" in batch.keys()) or (batch.get("M") and batch.get("M") != []):
            if batch.get("R"):
                for key in batch.get("R").keys():
                    try:
                        topic_name = key
                        data = batch.get("R")[key]
                        timestamp = None
                        records = list(function_map[topic_name]([(timestamp, data)], None))
                        records = {topic_name: records}
                        await self._func(records)
                        # await self._func(
                        #     topic_name = key,
                        #     data = batch.get("R")[key],
                        #     timestamp = None)
                    except Exception as e:
                        raise ParsingError(e)

            elif batch.get("M"):
                for data in batch.get("M"):
                    method = data["M"]
                    message = data["A"]

                    topic_name = message[0]
                    data = message[1]
                    timestamp = message[2]
                    records = list(function_map[topic_name]([(timestamp, data)], None))
                    records = {topic_name: records}

                    await self._func(records)
                    # await self._func(
                    #     topic_name = message[0],
                    #     data = message[1],
                    #     timestamp = message[2])