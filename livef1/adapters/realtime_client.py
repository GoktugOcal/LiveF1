import asyncio
import inspect

import time
from urllib.parse import urljoin

import requests
from websockets.exceptions import WebSocketException

from ..auth import login
from ..data_processing.etl import function_map
from .signalrcore import COMPLETION, connect
from ..utils.logger import logger
from ..utils.constants import (
    BASE_URL,
    SIGNALR_ENDPOINT,
    REALTIME_CALLBACK_DEFAULT_PARAMETERS
    )
from ..utils.exceptions import (
    AdapterError,
    ArgumentError,
    AuthenticationError,
    ParsingError
)

# seconds to wait before reconnecting; doubles after every failed attempt
RECONNECT_DELAY = 1
MAX_RECONNECT_DELAY = 30


class RealF1Client:
    """
    A client for managing real-time Formula 1 data streaming.

    The client connects to the live timing SignalR Core hub with the F1TV
    token from :func:`livef1.login`, signing in first if needed.

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
    _log_file : file object
        Log file object for writing messages.
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
        self.headers = {'User-Agent': 'BestHTTP'}

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
        Start the client and block until it is interrupted.
        """
        start = time.time()
        try:
            asyncio.run(self._run())
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt - exiting...")
        logger.info(f"Client have run for {(time.time() - start):.2f} seconds.")

    async def _run(self):
        """
        Keep a live timing connection open, reconnecting when it drops.
        """
        logger.info("Starting LiveF1 live timing client")
        delay = RECONNECT_DELAY
        force_login = False
        while True:
            try:
                async for _ in self._stream(force_login):
                    # connected and subscribed; reset the retry state
                    delay, force_login = RECONNECT_DELAY, False
                logger.warning(f"Live timing closed the connection. Reconnecting in {delay} s...")
            except AuthenticationError:
                if force_login:
                    raise
                logger.info("Live timing rejected the token. Signing in again...")
                force_login = True
                continue
            except (OSError, WebSocketException, requests.RequestException, asyncio.TimeoutError, AdapterError) as exc:
                logger.warning(f"Live timing connection failed ({exc}). Reconnecting in {delay} s...")
            await asyncio.sleep(delay)
            delay = min(delay * 2, MAX_RECONNECT_DELAY)

    async def _stream(self, force_login):
        """
        Connect, subscribe and dispatch messages until the connection closes.

        Yields once after subscribing, so that the caller knows the connection is up.
        """
        headers = {**self.headers, **login(force=force_login).header}
        async with await connect(self._connection_url, headers) as connection:
            await connection.invoke("Subscribe", [self.topics])
            logger.info(f"Connected to live timing, subscribed to: {', '.join(self.topics)}")
            yield
            async for frame in connection.messages():
                await self._dispatch(frame)

    async def _dispatch(self, frame):
        """
        Send the records of a hub frame to every registered handler.

        Parameters
        ----------
        frame : dict
            A SignalR Core frame: the ``Subscribe`` completion, holding a
            snapshot of every topic, or a ``feed`` invocation with
            ``[topic, data, timestamp]`` arguments.
        """
        if frame.get("type") == COMPLETION:
            if frame.get("error"):
                logger.error(f"Live timing subscription failed: {frame['error']}")
                return
            entries = [(topic, data, None) for topic, data in (frame.get("result") or {}).items()]
        elif frame.get("target") == "feed":
            arguments = frame.get("arguments") or []
            if len(arguments) < 2:
                return
            entries = [(arguments[0], arguments[1], arguments[2] if len(arguments) > 2 else None)]
        else:
            return

        for topic, data, timestamp in entries:
            results = await asyncio.gather(
                *(handler(topic, data, timestamp) for handler in list(self._handlers.values())),
                return_exceptions=True,
            )
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Live timing handler failed for {topic}: {result}")


class MessageHandlerTemplate:
    """
    A template for handling incoming live timing messages.

    Incoming topic data is parsed with `function_map` and the resulting
    records are passed to a user-defined function.

    Parameters
    ----------
    func : callable
        A user-defined asynchronous function that processes the parsed records
        from incoming messages. The function must accept the processed 
        records as its input.
    """
    def __init__(
        self,
        func
    ):
        self._func = func
    
    async def get(self, topic, data, timestamp):
        """
        Parse the data of a topic and invoke the handler function with ``{topic: records}``.

        Parameters
        ----------
        topic : str
            The topic name, e.g. ``"CarData.z"``.
        data : dict or str
            The topic data.
        timestamp : str or None
            The message timestamp; None for the initial snapshot.
        """
        try:
            records = list(function_map[topic]([(timestamp, data)], None))
        except Exception as e:
            raise ParsingError(f"Failed to parse {topic}: {e}") from e
        await self._func({topic: records})
