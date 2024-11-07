from .adapters import LivetimingF1adapters, livetimingF1_request
from .models import (
    Session,
    Season,
    Meeting
)
from .api import download_data
from .utils.helper import json_parser_for_objects
import urllib

def get_season(season: int) -> Season:
    """
    Retrieves the season data for the specified year.

    Args:
        season (int): The year of the season to retrieve.

    Returns:
        Season: A Season object containing all meetings and sessions for the specified season.
    """
    season_data = download_data(season_identifier=season)
    return Season(**json_parser_for_objects(season_data))

def get_meeting(season: int, location: str = None, meeting_no: int = None) -> Meeting:
    """
    Retrieves meeting data for a given season based on location or meeting number.

    Args:
        season (int): The year of the season to retrieve the meeting from.
        location (str, optional): The location of the meeting. Defaults to None.
        meeting_no (int, optional): The meeting number in the season. Defaults to None.

    Returns:
        Meeting: A Meeting object containing all sessions for the specified meeting.
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
    Retrieves a specific session from a meeting within a season based on location or meeting/session number.

    Args:
        season (int): The year of the season.
        location (str, optional): The location of the meeting. Defaults to None.
        meeting_no (int, optional): The meeting number in the season. Defaults to None.
        session (str, optional): The name of the session (e.g., "Practice 1"). Defaults to None.
        session_no (int, optional): The session number within the meeting. Defaults to None.

    Returns:
        Session: A Session object containing data about the specific session.
    """
    session_name = session
    season_obj = get_season(season=season)
    meeting = [meeting for meeting in season_obj.meetings if meeting.location == location][0]
    session_obj = [session for session in meeting.sessions if session.name == session_name][0]
    return session_obj
