# Standard Library Imports
from urllib.parse import urljoin

# Internal Project Imports
from .livetimingf1_adapter import livetimingF1_request
from ..utils.exceptions import livef1Exception

def download_data(
    season_identifier: int = None, 
    location_identifier: str = None, 
    session_identifier: str | int = None
):
    """
    Downloads and filters F1 data based on the provided season, location, and session identifiers.

    Parameters
    ----------
    
    season_identifier : :class:`int`
        The unique identifier for the F1 season. This is a required parameter.
    location_identifier : :class:`str`
        The location (circuit or country name) for filtering meetings (races).
    session_identifier : :class:`str`
        The session name (e.g., 'FP1', 'Qualifying') or key (integer) to filter a specific session within a meeting.
    
    Returns
    ----------
    dict
        The filtered dataset containing the requested season, meeting, or session data.
    
    Raises
    ----------
    livef1Exception
        Raised if any of the required parameters are missing or if no matching data is found.

    Examples
    -------------
    .. code-block:: python
    
       print("Hello World")

    """
    
    # Initialize a variable to store the final filtered data
    last_data = None

    # Ensure a season identifier is provided (mandatory)
    if season_identifier is None:
        raise livef1Exception("Please provide at least a `season_identifier`.")

    try:
        # Download full season data using the F1 API
        season_data = livetimingF1_request(urljoin(str(season_identifier) + "/", "Index.json"))
        last_data = season_data  # Default to entire season data initially

        # If a location (race circuit) is provided, filter the season data to find the specific meeting (race)
        if location_identifier:
            meeting_data = next(
                (meeting for meeting in season_data["Meetings"] if meeting["Location"] == location_identifier), 
                None
            )
            if meeting_data:
                last_data = meeting_data  # Update with filtered meeting data
            else:
                raise livef1Exception(f"Meeting at location '{location_identifier}' not found.")
        else:
            meeting_data = season_data["Meetings"]

        # If a session (e.g., FP1, Qualifying) is provided, further filter the meeting data
        if session_identifier:
            if isinstance(session_identifier, str):
                # Filter by session name (string match)
                session_data = next(
                    (session for session in meeting_data['Sessions'] if session['Name'] == session_identifier), 
                    None
                )
            elif isinstance(session_identifier, int):
                # Filter by session key (integer match)
                session_data = next(
                    (session for session in meeting_data['Sessions'] if session['Key'] == session_identifier), 
                    None
                )
            
            if session_data:
                last_data = session_data  # Update with filtered session data
            else:
                raise livef1Exception(f"Session with identifier '{session_identifier}' not found.")

    except Exception as e:
        # Catch any exception and wrap it in a custom livef1Exception
        raise livef1Exception(e) from e

    # Return the final filtered data (season, meeting, or session)
    return last_data
