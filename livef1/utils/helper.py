# Standard Library Imports
import base64
import collections
import datetime
import json
import zlib
from urllib.parse import urljoin
from typing import List, Dict, Union
from jellyfish import jaro_similarity, jaro_winkler_similarity
import re
from string import punctuation
import numpy as np
import pandas as pd

# Internal Project Imports
from .constants import *
from .logger import logger
from .exceptions import LiveF1Error
from ..adapters import LivetimingF1adapters

def build_session_endpoint(session_path):
    """
    Constructs a full endpoint URL for accessing session data.

    Parameters
    ----------
    session_path : str
        The path for the specific session data.

    Returns
    -------
    str
        The complete URL for the session endpoint.
    """
    return urljoin(urljoin(BASE_URL, STATIC_ENDPOINT), session_path)


def json_parser_for_objects(data: Dict) -> Dict:
    """
    Converts the keys of a dictionary to lowercase.

    Parameters
    ----------
    data : Dict
        The original dictionary with keys.

    Returns
    -------
    Dict
        A new dictionary with all keys converted to lowercase.
    """
    return {key.lower(): value for key, value in data.items()}


def get_data(path, stream):
    """
    Fetches data from a specified endpoint.

    Parameters
    ----------
    path : str
        The endpoint to retrieve data from.
    stream : bool
        Indicates whether to return a stream of records or a single response.

    Returns
    -------
    Union[dict, str]
        A dictionary of records if `stream` is True, else a string response.
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

    Parameters
    ----------
    path : str
        The endpoint to retrieve car data from.

    Returns
    -------
    dict
        A dictionary where keys are the first 12 characters of each record and values are the remaining data.
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

    Parameters
    ----------
    text : str
        The input text to be parsed.
    zipped : bool, optional
        Indicates if the input is a zipped string, by default False.

    Returns
    -------
    Union[str, dict]
        The parsed output as a dictionary if input is JSON, otherwise as a string.
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

    Parameters
    ----------
    hash_code : str
        The hash string to be parsed.

    Returns
    -------
    dict
        The decompressed and parsed data as a dictionary.
    """
    tl = 12  # Length of the key in the response.
    return parse(hash_code, zipped=True)


def parse_helper_for_nested_dict(info, record, prefix=""):
    """
    Recursively parses a nested dictionary and flattens it into a single-level dictionary.

    Parameters
    ----------
    info : dict
        The nested dictionary to parse.
    record : dict
        The record to which parsed information will be added.
    prefix : str, optional
        A prefix for keys in the flattened dictionary, by default "".

    Returns
    -------
    dict
        The updated record with flattened keys from the nested dictionary.
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

def identifer_text_format(text):
    """
    Formats text for comparison by splitting into words and removing stopwords.

    Parameters
    ----------
    text : str
        The input text to format.

    Returns
    -------
    list
        A list of words from the input text with stopwords removed.
    """
    querywords = re.split(rf'[\s{punctuation}]+', text.casefold())
    return [word for word in querywords if word not in QUERY_STOPWORDS]

def find_most_similar_vectorized(df, target):
    """
    Find the most similar string in a Pandas DataFrame using Jaccard and Jaro-Winkler similarity.

    Parameters
    ----------
    df : pd.DataFrame
        The DataFrame to search in.
    target : str
        The string to search for.

    Returns
    -------
    dict
        A dictionary containing:
            - "isFound" (int): 1 if a match is found, 0 otherwise.
            - "how" (str): The method used for matching ("jaccard" or "jaro").
            - "value" (str): The most similar value found.
            - "similarity" (float): The similarity score of the match.
            - "row" (int): The row index of the match.
            - "column" (str): The column name of the match.

    Raises
    ------
    livef1Exception
        If no match is found and suggestions are provided.
    """

    def jaccard_similarity(cell):
        """
        Calculates the Jaccard similarity between two sets of words.

        Parameters
        ----------
        cell : str
            The text to compare against the target.

        Returns
        -------
        float
            The Jaccard similarity score.
        """
        intersection_cardinality = len(
            set.intersection(
                *[
                    set(identifer_text_format(target)),
                    set(identifer_text_format(cell))
                ]
            )
        )
        union_cardinality = len(
            set.union(
                *[
                    set(identifer_text_format(target)),
                    set(identifer_text_format(cell))
                ]
            )
        )
        return intersection_cardinality/float(union_cardinality)

    def jarow_similarity(cell):
        """
        Calculates the Jaro-Winkler similarity between two strings.

        Parameters
        ----------
        cell : str
            The text to compare against the target.

        Returns
        -------
        float
            The Jaro-Winkler similarity score.
        """
        return jaro_winkler_similarity(
            " ".join(identifer_text_format(target)),
            " ".join(identifer_text_format(cell))
            )

    def argmax_n(arr: np.array, n: int, axis=None):
        """
        Finds the indices of the top-n maximum values in an array.

        Parameters
        ----------
        arr : np.array
            The array to search in.
        n : int
            The number of maximum values to find.
        axis : int, optional
            The axis to search along, by default None.

        Returns
        -------
        list
            A list of indices corresponding to the top-n maximum values.
        """
        argmaxes = []
        for _ in range(n):
            row, col = divmod(arr.argmax(), arr.shape[1])
            argmaxes.append(row)
            # arr = np.delete(arr, row, axis=0)
            arr[row,:] = 0
            # print(row, col)
        return argmaxes

    logger.debug(f"Searching of identifier '{target}' has started.")

    similarity_df = df.map(jaccard_similarity)
    jaccard_score = similarity_df.max().max()
    row, col = divmod(similarity_df.values.argmax(), similarity_df.shape[1])
    most_similar = df.iloc[row, col]


    if jaccard_score:
        # found_info = "\n".join([f"{SESSIONS_COLUMN_MAP[col]} : {df.reset_index().loc[row, col]}" for col in df.reset_index(drop=True).columns])
        # logger.info(f"Found at column '{(SESSIONS_COLUMN_MAP[df.columns[col]]).upper()}' as '{most_similar}'.")
        # logger.info(f"""Selected meeting/session is:\n{found_info}""")

        return {
            "isFound": 1,
            "how" : "jaccard",
            "value": most_similar,
            "similarity": jaccard_score,
            "row": df.iloc[row].name,
            "column": df.columns[col]
        }
    else:
        logger.info("The identifier couldn't be found.")

        jaro_df = df.map(jarow_similarity)
        jaro_score = jaro_df.max().max()

        if jaro_score >= 0.9:
            row, col = divmod(jaro_df.values.argmax(), jaro_df.shape[1])
            most_similar = df.iloc[row, col]
            logger.info(f"The identifier is very close to '{most_similar}' at column '{(SESSIONS_COLUMN_MAP[df.columns[col]]).upper()}'")
            # found_info = "\n".join([f"{SESSIONS_COLUMN_MAP[col]} : {df.reset_index().loc[row, col]}" for col in df.reset_index(drop=True).columns])
            # logger.info(f"""Selected meeting/session is:\n{found_info}""")

            return {
                "isFound": 1,
                "how" : "jaro",
                "value": most_similar,
                "similarity": jaro_score,
                "row": row,
                "column": df.columns[col]
            }

        else:
            poss_args = argmax_n(jaro_df.values, 3, axis=1)
            possible_df = df.iloc[poss_args]

            err_text = f"\nThe searched query '{target}' not found in the table. Did you mean one of these :\n\n"
            for idx, prow in possible_df.iterrows():
                for col in possible_df.columns:
                    err_text += f"\t{SESSIONS_COLUMN_MAP[col]} : {prow[col]}\n"
                # err_text += f"\t> Suggested search queries : {identifer_text_format(prow.meeting_name) + identifer_text_format(prow.meeting_circuit_shortname)}\n\n"
                err_text += f"\t> Suggested search queries : {[identifer_text_format(prow[col])for col in possible_df.columns if not col in EXCLUDED_COLUMNS_FOR_SEARCH_SUGGESTION]}\n\n"
            raise LiveF1Error(err_text)

            return {
                "isFound": 0,
                "how": None,
                "value": None,
                "similarity": None,
                "row": None,
                "column": None
            }

def print_found_model(df, key, cols):
    found_meeting_info = df.loc[[key], cols].drop_duplicates().iloc[0]
    found_info = "\n".join([f"\t{SESSIONS_COLUMN_MAP[col]} : {found_meeting_info[col]}" for col in cols])
    logger.info(f"""Selected meeting/session is:\n{found_info}""")


def to_datetime(var):
    if isinstance(var, pd.Series):
        return pd.to_datetime(var.values).tz_localize(None).round("ms")
    elif isinstance(var, np.ndarray):
        return pd.to_datetime(var).tz_localize(None).round("ms")
        