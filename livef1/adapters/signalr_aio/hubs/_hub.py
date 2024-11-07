#!/usr/bin/python
# -*- coding: utf-8 -*-

# signalr_aio/hubs/_hub.py
# Stanislav Lazarov

import asyncio
import time

class Hub:
    def __init__(self, name, connection):
        self.name = name
        self.server = HubServer(name, connection, self)
        self.client = HubClient(name, connection)


class HubServer:
    def __init__(self, name, connection, hub):
        self.name = name
        self.__connection = connection
        self.__hub = hub

    def invoke(self, method, *data):
        message = {
            'H': self.name,
            'M': method,
            'A': data,
            'I': self.__connection.increment_send_counter()
        }
        self.__connection.send(message)


class HubClient(object):
    def __init__(self, name, connection):
        self.name = name
        self.__handlers = {}
        self.__handler = lambda x: x

        async def handle(**data):
            try:
                asyncio.gather(*[handler(data) for handler in list(self.__handlers.values())])
            except Exception as e:
                print(e)

        connection.received += handle

    def on(self, method, handler):
        if method not in self.__handlers:
            self.__handlers[method] = handler
    
    # def on(self, handler):
    #     self.__handler = handler

    def off(self, method, handler):
        if method in self.__handlers:
            self.__handlers[method] -= handler
