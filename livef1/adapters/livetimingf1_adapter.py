# Standard Library Imports
import json
import urllib

# Third-Party Library Imports
import requests
from typing import List, Dict

# Internal Project Imports
from ..utils.constants import *


class LivetimingF1adapters:
    """
    Adapter class for interacting with the F1 Livetiming API.
    
    This class builds and sends HTTP requests to retrieve data from the static 
    Livetiming API, using a base URL and various endpoints.
    """

    def __init__(self):
        """
        Initializes the LivetimingF1adapters class with the base URL for the Livetiming API.
        
        The base URL is constructed using the BASE_URL and STATIC_ENDPOINT constants.
        """
        self.url = urllib.parse.urljoin(BASE_URL, STATIC_ENDPOINT)  # Base URL for F1 Livetiming API

    def get(self, endpoint: str, header: Dict = None):
        """
        Sends a GET request to the specified endpoint.

        Parameters:
        - endpoint (str): The specific API endpoint to append to the base URL.
        - header (Dict, optional): HTTP headers to send with the request (default is None).
        
        Returns:
        - str: The response content decoded as a UTF-8 string.
        """
        req_url = urllib.parse.urljoin(self.url, endpoint)  # Build the full request URL
        response = requests.get(
            url=req_url,
            headers=header
        )

        # Decode the response content to handle special UTF-8 encoding with BOM
        res_text = response.content.decode('utf-8-sig')
        return res_text

def livetimingF1_request(url):
    """
    Wrapper function to perform a GET request to the Livetiming F1 API.

    Parameters:
    - url (str): The full URL to request.

    Returns:
    - dict: Parsed JSON response from the API.
    """
    adapters = LivetimingF1adapters()  # Initialize the adapter class
    response = adapters.get(url)  # Perform the GET request
    data = json.loads(response)  # Parse the JSON response
    return data

def livetimingF1_getdata(url, stream):
    """
    Retrieves data from the Livetiming F1 API, either as a stream of records or a static response.

    Parameters:
    - url (str): The full URL to request.
    - stream (bool): If True, treats the response as a stream of newline-separated records.
                     If False, treats it as a static JSON response.

    Returns:
    - dict: A dictionary containing parsed data. If streaming, each line is parsed and split.
    """
    adapters = LivetimingF1adapters()  # Initialize the adapter class
    res_text = adapters.get(endpoint=url)  # Perform the GET request

    if stream:
        # Streamed data is split by newline and each record is processed
        records = res_text.split('\r\n')[:-1]  # Remove the last empty line
        tl = 12  # Record key length (first 12 characters are the key)
        # Return a dictionary of keys and their parsed JSON values
        return dict((r[:tl], json.loads(r[tl:])) for r in records)
    else:
        # If not streaming, parse the entire response as JSON
        records = json.loads(res_text)
        return records
