import logging
import asyncio
import concurrent
import requests
import inspect


import time
import json
from urllib.parse import urljoin

from ..adapters.signalr_aio._connection import Connection
from ..utils.constants import (
    DEFAULT_METHOD,
    BASE_URL,
    SIGNALR_ENDPOINT,
    REALTIME_CALLBACK_DEFAULT_PARAMETERS
    )

import random

class RealF1Client:

    def __init__(
        self, 
        topics,
        log_file_name = "./realtime_client_logs.txt",
        log_file_mode = "w",
        test = False
        ):

        self._connection_url = urljoin(BASE_URL, SIGNALR_ENDPOINT)
        self.headers = {
            'User-agent': 'BestHTTP',
            'Accept-Encoding': 'gzip, identity',
            'Connection': 'keep-alive, Upgrade'}

        if isinstance(topics, str): self.topics = [topics]
        elif isinstance(topics, list): self.topics = topics
        else: raise ValueError("You need to give list of topics you want to subscribe")
        
        self._log_file_name = log_file_name
        self._log_file_mode = log_file_mode
        self._test = test

        if self._test: self._log_file = open(self._log_file_name, self._log_file_mode)

        self._handlers = {}

    def _create_session(self):
        session = requests.Session()
        session.headers = self.headers
        return session
    
    async def _on_message(self, msg):
        self._t_last_message = time.time()
        loop = asyncio.get_running_loop()
        try:
            with concurrent.futures.ThreadPoolExecutor() as pool:
                await loop.run_in_executor(
                    pool, print, str(msg)
                )
        except Exception:
            print("Exception while writing message")
    
    async def _test_on(self, msg):
        # await asyncio.sleep(self.C)
        self._t_last_message = time.time()
        loop = asyncio.get_running_loop()
        try:
            with concurrent.futures.ThreadPoolExecutor() as pool:
                await loop.run_in_executor(
                    pool, print, type(msg)
                )
        except Exception:
            print("Exception while writing message")

    async def _file_logger(self, msg):
        # if self._test and msg != {} and msg:
        if msg != {} and msg:
            self._log_file.write(str(msg) + '\n')
            self._log_file.flush()
        
    def on_message(self, method, handler):
        if method not in self._handlers:
            func = MessageHandlerTemplate(handler).get
            self._handlers[method] = func
            # self._handlers[method] = handler

    def callback(self, method):
        def inner(func):
            # Check if the provided function has the required arguments
            has_args = set(REALTIME_CALLBACK_DEFAULT_PARAMETERS) == set(inspect.signature(func).parameters.keys())
            args_diff = set(REALTIME_CALLBACK_DEFAULT_PARAMETERS).difference(set(inspect.signature(func).parameters.keys()))
            if not has_args:
                raise TypeError(f"The provided callback function does not have following required arguments. {args_diff}")
            else:
                # Register the function as a handler for the given method
                self.on_message(method,func)
                print(f"Custom callback method with '{method}' has successfully inserted.")
            return func
        return inner

    def run(self):
        self._async_engine_run()

    def _async_engine_run(self):
        try:
            asyncio.run(self._async_run())
        except KeyboardInterrupt:
            print("Keyboard interrupt - exiting...")
    
    async def _async_run(self):
        print(f"Starting FastF1 live timing client")
        await asyncio.gather(
            asyncio.ensure_future(self._forever_check()),
            asyncio.ensure_future(self._run())
            )
        print("Exiting...")

    async def _forever_check(self):
        while True:
            # print("I am here...")
            await asyncio.sleep(1)
        
    def _sync_engine_run(self):
        pass
    
    def _sync_engine(self):
        pass
    
    async def _run(self):
        # Create connection
        self._connection = Connection(self._connection_url, session=self._create_session())
        # Register hub
        hub = self._connection.register_hub('Streaming')
        # Set default message handler
        # hub.client.on('feed', self._on_message)
        for method, handler in self._handlers.items():
            hub.client.on(method, handler)

        # Subscribe topics in interest
        hub.server.invoke("Subscribe", self.topics)
        # Start the client
        loop = asyncio.get_event_loop()
        executor = concurrent.futures.ThreadPoolExecutor()
        await loop.run_in_executor(executor, self._connection.start)


class MessageHandlerTemplate:
    def __init__(
        self,
        func
    ):
        self._func = func
    
    async def get(self, msg):
        batch = msg

        if ("R" in batch.keys()) or (batch.get("M") and batch.get("M") != []):
            if batch.get("R"):
                for key in batch.get("R").keys():

                    try:
                        await self._func(
                            topic_name = key,
                            data = batch.get("R")[key],
                            timestamp = None)
                    except Exception as e:
                        print(e)

                    
                    # await self._func([data_key, data])

            elif batch.get("M"):
                for data in batch.get("M"):
                    method = data["M"]
                    message = data["A"]

                    await self._func(
                        topic_name = message[0],
                        data = message[1],
                        timestamp = message[2])

                    # await self._func(message)