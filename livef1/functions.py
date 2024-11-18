from .adapters import LivetimingF1adapters, livetimingF1_request
from .models import (
    Session,
    Season,
    Meeting
)
from .api import download_data
from .utils.helper import json_parser_for_objects

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

def get_meeting(season: int, location: str = None, meeting_no: int = None) -> Meeting:
    """
    Retrieve data for a specific meeting in a given season.

    Parameters
    ----------
    season : :class:`int`
        The year of the season to retrieve the meeting from.
    location : :class:`str`, optional
        The location (e.g., circuit name) of the meeting. Defaults to None.
    meeting_no : :class:`int`, optional
        The sequential number of the meeting within the season. Defaults to None.

    Returns
    -------
    Meeting
        A `Meeting` object containing sessions and metadata for the specified meeting.

    Raises
    ------
    livef1Exception
        If the meeting cannot be found based on the provided parameters.
    """
    meeting_data = download_data(season_identifier=season, location_identifier=location)
    return Meeting(**json_parser_for_objects(meeting_data))

def get_session(
    season: int, 
    location: str = None, 
    meeting_no: int = None, 
    session: str = None, 
    session_no: int = None
) -> Session:
    """
    Retrieve data for a specific session within a meeting and season.

    Parameters
    ----------
    season : :class:`int`
        The year of the season.
    location : :class:`str`, optional
        The location (e.g., circuit name) of the meeting. Defaults to None.
    meeting_no : :class:`int`, optional
        The sequential number of the meeting within the season. Defaults to None.
    session : :class:`str`, optional
        The name of the session (e.g., "Practice 1", "Qualifying"). Defaults to None.
    session_no : :class:`int`, optional
        The sequential number of the session within the meeting. Defaults to None.

    Returns
    -------
    Session
        A `Session` object containing data about the specified session.

    Raises
    ------
    livef1Exception
        If the session cannot be found based on the provided parameters.
    """
    session_name = session
    season_obj = get_season(season=season)
    meeting = [meeting for meeting in season_obj.meetings if meeting.location == location][0]
    session_obj = [session for session in meeting.sessions if session.name == session_name][0]
    return session_obj
