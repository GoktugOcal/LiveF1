from .adapters import LivetimingF1adapters, livetimingF1_request
from .models import (
    Session,
    Season,
    Meeting
)
from .adapters import download_data
from .utils.helper import json_parser_for_objects, find_most_similar_vectorized, print_found_model
from .utils.logger import logger
from .utils.exceptions import *
from .utils.constants import SESSIONS_COLUMN_MAP

from datetime import datetime

__version__ = "0.1.48"

def get_season(season: int) -> Season:
    """
    Retrieve data for a specified Formula 1 season.

    Parameters
    ----------
    season : :class:`int`
        The year of the season to retrieve.

    Returns
    -------
    Season
        A `Season` object containing all meetings and sessions for the specified year.

    Raises
    ------
    livef1Exception
        If no data is available for the specified season.
    """
    logger.debug(f"Getting season {season}.")
    season_data = download_data(season_identifier=season)
    season = Season(**json_parser_for_objects(season_data))
    logger.debug("Got the season.")
    return season

def get_meeting(
    season: int,
    meeting_identifier: str = None,
    meeting_key: int = None
    ) -> Meeting:
    """
    Retrieve data for a specific meeting in a given season.

    Parameters
    ----------
    season : :class:`int`
        The year of the season to retrieve the meeting from.
    meeting_identifier : :class:`str`
        The identifier (e.g., circuit name, grand prix name) of the meeting.
        The identifier is going to be searched in the season's meeting table columns:
            - "Meeting Official Name"
            - "Meeting Name"
            - "Circuit Short Name"
        Therefore, it is suggested to use keywords that is distinguishable among meetings.
        Another suggestion is using circuit names for querying.
    meeting_key : :class:`int`
        The key of the meeting to get the desired meeting whose key is matching.

    Returns
    -------
    Meeting
        A `Meeting` object containing sessions and metadata for the specified meeting.

    Raises
    ------
    livef1Exception
        If the meeting cannot be found based on the provided parameters.
    """

    # Check if sufficient arguments have been provided
    if (meeting_identifier == None) and (meeting_key == None):
        try:
            raise ArgumentError(f"One of the following arguments needs to be defined: 'meeting_identifier', 'meeting_key'.")
        except ArgumentError as e:
            logger.error(f"An error occured {e}")
            raise

    season_obj = get_season(season=season)
    required_cols = ["meeting_offname","meeting_name","meeting_circuit_shortname"]
    search_df_season = season_obj.season_table.reset_index()[required_cols].drop_duplicates()

    if meeting_identifier:
        logger.debug("Getting meeting by meeting identifier.")
        result_meeting = find_most_similar_vectorized(search_df_season, meeting_identifier)
        meeting_key = season_obj.season_table.iloc[result_meeting["row"]].name
    
    elif meeting_key:
        logger.debug("Getting meeting by meeting key.")
        pass

    meeting_obj = [meeting for meeting in season_obj.meetings if meeting.key == meeting_key][0]

    # found_meeting_info = season_obj.season_table.loc[[meeting_key], required_cols].drop_duplicates().iloc[0]
    # found_info = "\n".join([f"{SESSIONS_COLUMN_MAP[col]} : {found_meeting_info[col]}" for col in required_cols])
    # logger.info(f"""Selected meeting/session is:\n{found_info}""")

    print_found_model(
        df = season_obj.season_table,
        key = meeting_key,
        cols = required_cols
    )
    logger.info("Got the meeting.")

    return meeting_obj

def get_session(
    season: int, 
    meeting_identifier: str = None,
    session_identifier: str = None,
    meeting_key: int = None,
    session_key: int = None
) -> Session:
    """
    Retrieve data for a specific session within a meeting and season.

    Parameters
    ----------
    season : :class:`int`
        The year of the season.
    meeting_identifier : :class:`str`
        The identifier (e.g., circuit name, grand prix name) of the meeting.
        The identifier is going to be searched in the season's meeting table columns:
            - "Meeting Official Name"
            - "Meeting Name"
            - "Circuit Short Name"
        Therefore, it is suggested to use keywords that is distinguishable among meetings.
        Another suggestion is using circuit names for querying.
    meeting_key : :class:`int`
        The key of the meeting to get the desired meeting whose key is matching.
    session_identifier : :class:`str`
        The identifier of the session (e.g., "Practice 1", "Qualifying").
        The identifier is going to be searched in the meeting's sessions table.
    session_key : :class:`int`
        The key of the session to get the desired session whose key is matching.

    Returns
    -------
    Session
        A `Session` object containing data about the specified session.

    Raises
    ------
    livef1Exception
        If the session cannot be found based on the provided parameters.
    """

    # Check if sufficient arguments have been provided
    if (session_identifier == None) and (session_key == None):
        try:
            raise ArgumentError(f"One of the following arguments needs to be defined: 'session_identifier', 'session_key'.")
        except ArgumentError as e:
            logger.error(f"An error occured {e}")
            raise

    meeting_obj = get_meeting(
        season=season,
        meeting_identifier=meeting_identifier,
        meeting_key=meeting_key
    )
    required_cols = ["session_name"]
    search_df_season = meeting_obj.sessions_table.reset_index()[required_cols].drop_duplicates()

    if session_identifier:
        logger.debug("Getting session by identifier.")
        result_session = find_most_similar_vectorized(search_df_season, session_identifier)
        session_key = meeting_obj.sessions_table.iloc[result_session["row"]].name

    elif session_key:
        logger.debug("Getting session by key.")
        pass

    session_obj = [session for session in meeting_obj.sessions if session.key == session_key][0]
    print_found_model(
        df = meeting_obj.sessions_table,
        key = session_key,
        cols = required_cols
    )
    logger.info("The session was received successfully.")

    session_obj.load_session_data()
    return session_obj