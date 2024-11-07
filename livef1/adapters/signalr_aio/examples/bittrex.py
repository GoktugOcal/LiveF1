#!/usr/bin/python
# -*- coding: utf-8 -*-

# Stanislav Lazarov

# A practical example showing how to connect to Bittrex
# Requires Python3.5+
# pip install git+https://github.com/slazarov/python-signalr-client.git

from signalr_aio import Connection
from base64 import b64decode
from zlib import decompress, MAX_WBITS
import json


async def process_message(message):
    deflated_msg = decompress(b64decode(message), -MAX_WBITS)
    return json.loads(deflated_msg.decode())


# Create debug message handler.
async def on_debug(**msg):
    # In case of 'queryExchangeState'
    if 'R' in msg and type(msg['R']) is not bool:
        decoded_msg = await process_message(msg['R'])
        print(decoded_msg)


# Create error handler
async def on_error(msg):
    print(msg)


# Create hub message handler
async def on_message(msg):
    decoded_msg = await process_message(msg[0])
    print(decoded_msg)


if __name__ == "__main__":
    # Create connection
    # Users can optionally pass a session object to the client, e.g a cfscrape session to bypass cloudflare.
    connection = Connection('https://beta.bittrex.com/signalr', session=None)

    # Register hub
    hub = connection.register_hub('c2')

    # Assign debug message handler. It streams unfiltered data, uncomment it to test.
    connection.received += on_debug

    # Assign error handler
    connection.error += on_error

    # Assign hub message handler
    hub.client.on('uE', on_message)
    hub.client.on('uS', on_message)

    # Send a message
    hub.server.invoke('SubscribeToExchangeDeltas', 'BTC-ETH')
    hub.server.invoke('SubscribeToSummaryDeltas')
    hub.server.invoke('queryExchangeState', 'BTC-NEO')

    # Start the client
    connection.start()
