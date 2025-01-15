# Standard Library Imports
import json
import urllib

# Third-Party Library Imports
import requests
from typing import List, Dict

# Internal Project Imports
from ..utils.constants import *
from ..utils.logger import logger
from ..utils.exceptions import (
    AdapterError,
    InvalidEndpointError,
    ParsingError
)

__all__ = [
    "LivetimingF1adapters",
    "livetimingF1_request",
    "livetimingF1_getdata"
]


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

        Parameters
        ----------
            endpoint : :class:`str`
                The specific API endpoint to append to the base URL.
            header : :class:`dict`
                HTTP headers to send with the request (default is None).
        
        Returns
        ----------
        - str: The response content decoded as a UTF-8 string.
        """

        try:
            req_url = urllib.parse.urljoin(self.url, endpoint)  # Build the full request URL
            logger.debug(f"Sending GET request to URL: {req_url}")
            response = requests.get(
                url=req_url,
                headers=header,
                timeout=300  # Timeout added for robustness
            )
            response.raise_for_status()

            # Decode response
            try:
                res_text = response.content.decode('utf-8-sig')
            except UnicodeDecodeError as decode_err:
                logger.error(f"Failed to decode response: {decode_err}", exc_info=True)
                raise DataDecodingError(f"Failed to decode response: {decode_err}") from decode_err

            return res_text
        except requests.exceptions.Timeout as timeout_err:
            logger.error(f"Request timed out for URL: {req_url}", exc_info=True)
            raise TimeoutError(f"Request timed out: {timeout_err}") from timeout_err
        except requests.exceptions.ConnectionError as conn_err:
            logger.error(f"Connection failed for URL: {req_url}", exc_info=True)
            raise ConnectionError(f"Connection failed: {conn_err}") from conn_err
        except requests.exceptions.HTTPError as http_err:
            if response.status_code in [403,404]:
                logger.error(f"Endpoint not found: {req_url}", exc_info=True)
                raise InvalidEndpointError(f"Endpoint not found: {endpoint}") from http_err
            else:
                logger.error(f"HTTP error occurred for URL {req_url}: {http_err}", exc_info=True)
                raise AdapterError(f"HTTP error occurred: {http_err}") from http_err
        except Exception as e:
            logger.critical(f"Unexpected error for URL {req_url}: {e}", exc_info=True)
            raise AdapterError(f"An unexpected error occurred: {e}") from e

def livetimingF1_request(url):
    """
    Wrapper function to perform a GET request to the Livetiming F1 API.

    Parameters
    ----------
        url : :class:`str`
            The full URL to request.

    Returns
    ----------
        dict
            Parsed JSON response from the API.
    """
    adapters = LivetimingF1adapters()  # Initialize the adapter class
    response = adapters.get(url)  # Perform the GET request
    try:
        data = json.loads(response)  # Parse the JSON response
    except:
        logger.error("Error parsing request .", exc_info=True)
        raise ParsingError(f"Error parsing request: {parse_err}") from parse_err
    return data

def livetimingF1_getdata(url, stream):
    """
    Retrieves data from the Livetiming F1 API, either as a stream of records or a static response.

    Parameters
    ----------
        url : :class:`str`
            The full URL to request.
        stream : :class:`bool`
            If True, treats the response as a stream of newline-separated records.
            If False, treats it as a static JSON response.

    Returns
    ----------
        dict
            A dictionary containing parsed data. If streaming, each line is parsed and split.
    """
    adapters = LivetimingF1adapters()  # Initialize the adapter class
    res_text = adapters.get(endpoint=url)  # Perform the GET request

    if stream:
        try:
            # Streamed data is split by newline and each record is processed
            records = res_text.split('\r\n')[:-1]  # Remove the last empty line
            tl = 12  # Record key length (first 12 characters are the key)
            # Return a dictionary of keys and their parsed JSON values
            parsed_data = list((r[:tl], json.loads(r[tl:])) for r in records)
            logger.debug("Successfully parsed streamed data.")
            return parsed_data
        except (json.JSONDecodeError, IndexError) as parse_err:
            logger.error("Error parsing streamed data.", exc_info=True)
            raise ParsingError(f"Error parsing streamed data: {parse_err}") from parse_err
    else:
        try:
            # If not streaming, parse the entire response as JSON
            records = json.loads(res_text)
            logger.debug("Successfully parsed static JSON data.")
            return records
        except json.JSONDecodeError as parse_err:
            logger.error("Error parsing static JSON data.", exc_info=True)
            raise ParsingError(f"Error parsing static JSON data: {parse_err}") from parse_err
