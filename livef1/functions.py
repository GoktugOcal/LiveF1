from .adapters import LivetimingF1adapters, livetimingF1_request
from .models import (
    Session,
    Season,
    Meeting
)
from .api import download_data
from .utils.helper import json_parser_for_objects, find_most_similar_vectorized

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
    season_data = download_data(season_identifier=season)
    return Season(**json_parser_for_objects(season_data))

def get_meeting(
    season: int,
    meeting_identifier: str) -> Meeting:
    """
    Retrieve data for a specific meeting in a given season.

    Parameters
    ----------
    season : :class:`int`
        The year of the season to retrieve the meeting from.
    meeting_identifier : :class:`str`
        The location (e.g., circuit name) of the meeting.

    Returns
    -------
    Meeting
        A `Meeting` object containing sessions and metadata for the specified meeting.

    Raises
    ------
    livef1Exception
        If the meeting cannot be found based on the provided parameters.
    """
    # session_name = session
    season_obj = get_season(season=season)

    search_df_season = season_obj.meetings_table[["meeting_offname","meeting_name","meeting_circuit_shortname"]]
    result_meeting = find_most_similar_vectorized(search_df_season, meeting_identifier)
    meeting_code = season_obj.meetings_table.iloc[result_meeting["row"]].meeting_code
    meeting_obj = [meeting for meeting in season_obj.meetings if meeting.code == meeting_code][0]

    return meeting_obj

    # meeting_data = download_data(season_identifier=season, location_identifier=location)
    # return Meeting(**json_parser_for_objects(meeting_data))

def get_session(
    season: int, 
    meeting_identifier: str,
    session_identifier: str
) -> Session:
    """
    Retrieve data for a specific session within a meeting and season.

    Parameters
    ----------
    season : :class:`int`
        The year of the season.
    meeting_identifier : :class:`str`
        The location (e.g., circuit name) of the meeting.
    meeting_no : :class:`int`, optional
        The sequential number of the meeting within the season. Defaults to None.
    session_identifier : :class:`str`
        The name of the session (e.g., "Practice 1", "Qualifying").

    Returns
    -------
    Session
        A `Session` object containing data about the specified session.

    Raises
    ------
    livef1Exception
        If the session cannot be found based on the provided parameters.
    """

    meeting_obj = get_meeting(
        season,
        meeting_identifier
    )
    # # session_name = session
    # season_obj = get_season(season=season)

    # search_df_season = season_obj.meetings_table[["meeting_offname","meeting_name","meeting_circuit_shortname"]]
    # result_meeting = find_most_similar_vectorized(search_df_season, meeting_identifier)
    # meeting_code = season_obj.meetings_table.iloc[result_meeting["row"]].meeting_code
    # meeting_obj = [meeting for meeting in season_obj.meetings if meeting.code == meeting_code][0]

    search_df_season = meeting_obj.sessions_table[["session_name"]]
    result_session = find_most_similar_vectorized(search_df_season, session_identifier)
    session_name = meeting_obj.sessions_table.iloc[result_session["row"]].session_name
    session_obj = [session for session in meeting_obj.sessions if session.name == session_name][0]

    return session_obj