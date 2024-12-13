import logging

logging.basicConfig(
    format="%(asctime)s - %(levelname)s: %(message)s"
)
logger = logging.getLogger('SignalR')
logger.setLevel(logging.INFO)

import asyncio

from livef1.adapters.realtime_client import RealF1Client
from livef1.utils.constants import session_index
from livef1.data_processing.etl import livef1SessionETL

topics = list(session_index["Feeds"].keys())
topics = ["CarData.z", "SessionInfo"]

client = RealF1Client(
    topics = topics,
    log_file_name="./basic_test_new.json"
)

# @client.callback("printer")
# async def print_callback(
#     topic_name,
#     data,
#     timestamp
#     ):
#     function_map = livef1SessionETL(None).function_map
#     print("goktugo41", list(function_map[topic_name]({timestamp: data}, None)))

# @client.callback("logger")
# async def print_callback(topic_name,
#     data,
#     timestamp
#     ):
#     function_map = livef1SessionETL(None).function_map
#     for record in function_map[topic_name]({timestamp: data}, None):
#         await client._file_logger(record)

# @client.callback("new one")
# async def print_callback(
#     records
#     ):
#     print(records)

client.run()






# async def func(msg):
#     topic_name = msg[0]
#     data = msg[1]
#     function_map = livef1SessionETL(None).function_map
#     print("goktugo41", list(function_map[topic_name]({None: data}, None)))