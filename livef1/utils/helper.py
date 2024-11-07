# Standard Library Imports
import base64
import collections
import datetime
import json
import zlib
from urllib.parse import urljoin
from typing import List, Dict, Union

# Internal Project Imports
from .constants import *
from ..adapters import LivetimingF1adapters

def build_session_endpoint(session_path):
    """
    Constructs a full endpoint URL for accessing session data.

    Args:
        session_path (str): The path for the specific session data.

    Returns:
        str: The complete URL for the session endpoint.
    """
    return urljoin(urljoin(BASE_URL, STATIC_ENDPOINT), session_path)


def json_parser_for_objects(data: Dict) -> Dict:
    """
    Converts the keys of a dictionary to lowercase.

    Args:
        data (Dict): The original dictionary with keys.

    Returns:
        Dict: A new dictionary with all keys converted to lowercase.
    """
    return {key.lower(): value for key, value in data.items()}


def get_data(path, stream):
    """
    Fetches data from a specified endpoint.

    Args:
        path (str): The endpoint to retrieve data from.
        stream (bool): Indicates whether to return a stream of records or a single response.

    Returns:
        dict or str: A dictionary of records if stream is True, else a string response.
    """
    adapters = LivetimingF1adapters()
    endpoint = path
    res_text = adapters.get(endpoint=endpoint)

    if stream:
        records = res_text.split('\r\n')[:-1]  # Split response into lines, ignoring the last empty line.
        tl = 12  # Length of the key in the response.
        return dict((r[:tl], r[tl:]) for r in records)
    else:
        return res_text  # Return the full response text if not streaming.


def get_car_data_stream(path):
    """
    Fetches car data from a specified endpoint and returns it as a dictionary.

    Args:
        path (str): The endpoint to retrieve car data from.

    Returns:
        dict: A dictionary where keys are the first 12 characters of each record and values are the remaining data.
    """
    adapters = LivetimingF1adapters()
    endpoint = path
    res_text = adapters.get(endpoint=endpoint)
    records = res_text.split('\r\n')[:-1]  # Split response into lines, ignoring the last empty line.

    tl = 12  # Length of the key in the response.
    return dict((r[:tl], r[12:]) for r in records)


def parse(text: str, zipped: bool = False) -> Union[str, dict]:
    """
    Parses a given text input and decompresses it if necessary.

    Args:
        text (str): The input text to be parsed.
        zipped (bool): Indicates if the input is a zipped string.

    Returns:
        Union[str, dict]: The parsed output as a dictionary if input is JSON, otherwise as a string.
    """
    if text[0] == '{':  # Check if the text is in JSON format.
        return json.loads(text)  # Return parsed JSON as a dictionary.
    if text[0] == '"':  # Check if the text is a quoted string.
        text = text.strip('"')  # Remove surrounding quotes.
    if zipped:
        # Decompress the zipped base64 string and parse it.
        text = zlib.decompress(base64.b64decode(text), -zlib.MAX_WBITS)
        return parse(text.decode('utf-8-sig'))
    return text  # Return the text as is if it's not zipped.


def parse_hash(hash_code):
    """
    Parses a hashed string and decompresses it.

    Args:
        hash_code (str): The hash string to be parsed.

    Returns:
        dict: The decompressed and parsed data as a dictionary.
    """
    tl = 12  # Length of the key in the response.
    return parse(hash_code, zipped=True)


def parse_helper_for_nested_dict(info, record, prefix=""):
    """
    Recursively parses a nested dictionary and flattens it into a single level dictionary.

    Args:
        info (dict): The nested dictionary to parse.
        record (dict): The record to which parsed information will be added.
        prefix (str): A prefix for keys in the flattened dictionary.

    Returns:
        dict: The updated record with flattened keys from the nested dictionary.
    """
    for info_k, info_v in info.items():
        if isinstance(info_v, list):
            # Flatten list entries into the record with incremental suffixes.
            record = {**record, **{**{info_k + "_" + str(sector_no + 1) + "_" + k: v 
                                      for sector_no in range(len(info_v)) 
                                      for k, v in info_v[sector_no].items()}}}
        elif isinstance(info_v, dict):
            # Recursively parse nested dictionaries.
            record = parse_helper_for_nested_dict(info_v, record, prefix=prefix + info_k + "_")
        else:
            record = {**record, **{prefix + info_k: info_v}}  # Add scalar values to the record.
    return record
