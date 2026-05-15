# Standard Library Imports
from urllib.parse import urljoin
from pandas import to_datetime

# Internal Project Imports
from .livetimingf1_adapter import livetimingF1_request
from ..utils.exceptions import livef1Exception
from ..utils.helper import relocate_tz
from .jolpicaf1_adapter import jolpica_client


def merge_meetings(
    meetings_livetiming: dict,
    meetings_jolpica: dict
):
    """
    Merges meetings from Livetiming and Jolpica APIs.
    """
    live_meetings = {}
    for meeting in meetings_livetiming:
        name = meeting["Name"]
        if name in live_meetings: live_meetings[name + " 2"] = meeting
        else: live_meetings[name] = meeting
    meetings_livetiming = live_meetings
    meetings_jolpica = {race.race_name: race for race in meetings_jolpica}

    all_meetings = []
    # First, the meetings that are not in the Jolpica data
    live_only_meeting_keys = set(meetings_livetiming.keys()) - set(meetings_jolpica.keys())
    for key in live_only_meeting_keys:
        meeting = meetings_livetiming[key]
        meeting["round"] = 0
        all_meetings.append(meeting)
    
    # Second, the meetings that are in both data sources
    live_and_jol_meeting_keys = set(meetings_livetiming.keys()) & set(meetings_jolpica.keys())
    for key in live_and_jol_meeting_keys:
        meeting = meetings_livetiming[key]
        jol_meeting = meetings_jolpica[key]
        meeting["round"] = jol_meeting.round
        meeting["url"]  = jol_meeting.url
        meeting["Circuit"] = {None: None, **meeting["Circuit"], **jol_meeting.circuit.to_dict()}
        all_meetings.append(meeting)

    # Third, the meetings that are only in the Jolpica data
    jol_only_meeting_keys = set(meetings_jolpica.keys()) - set(meetings_livetiming.keys())
    for key in jol_only_meeting_keys:
        new_meeting = {}
        meeting = meetings_jolpica[key]

        new_meeting["Sessions"] = []
        if "FirstPractice" in meeting.to_dict().keys():
            new_meeting["Sessions"].append({
                "Key": "J" + meeting.round + "P1",
                "Type": "Practice",
                "Number": 1,
                "Name": "Practice 1",
                "StartDate": relocate_tz(
                    to_datetime(meeting.date + "T" + meeting.time),
                    source_tz = "UTC",
                    target_location = meeting.circuit.location.country).strftime("%Y-%m-%dT%H:%M:%S")
            })
        if "SecondPractice" in meeting.to_dict().keys():
            new_meeting["Sessions"].append({
                "Key": "J" + meeting.round + "P2",
                "Type": "Practice",
                "Number": 2,
                "Name": "Practice 2",
                "StartDate": relocate_tz(
                    to_datetime(meeting.date + "T" + meeting.time),
                    source_tz = "UTC",
                    target_location = meeting.circuit.location.country).strftime("%Y-%m-%dT%H:%M:%S")
            })
        if "ThirdPractice" in meeting.to_dict().keys():
            new_meeting["Sessions"].append({
                "Key": "J" + meeting.round + "P3",
                "Type": "Practice",
                "Number": 3,
                "Name": "Practice 3",
                "StartDate": relocate_tz(
                    to_datetime(meeting.third_practice.date + "T" + meeting.third_practice.time),
                    source_tz = "UTC",
                    target_location = meeting.circuit.location.country).strftime("%Y-%m-%dT%H:%M:%S")
            })
        if "Qualifying" in meeting.to_dict().keys():
            new_meeting["Sessions"].append({
                "Key": "J" + meeting.round + "Q",
                "Type": "Qualifying",
                "Name": "Qualifying",
                "StartDate": relocate_tz(
                    to_datetime(meeting.qualifying.date + "T" + meeting.qualifying.time),
                    source_tz = "UTC",
                    target_location = meeting.circuit.location.country).strftime("%Y-%m-%dT%H:%M:%S")
            })
        if "Sprint" in meeting.to_dict().keys():
            new_meeting["Sessions"].append({
                "Key": "J" + meeting.round + "S",
                "Type": "Race",
                "Number": -1,
                "Name": "Sprint",
                "StartDate": relocate_tz(
                    to_datetime(meeting.sprint.date + "T" + meeting.sprint.time),
                    source_tz = "UTC",
                    target_location = meeting.circuit.location.country).strftime("%Y-%m-%dT%H:%M:%S")
            })
        if "SprintQualifying" in meeting.to_dict().keys():
            new_meeting["Sessions"].append({
                "Key": "J" + meeting.round + "SQ",
                "Type": "Qualifying",
                "Number": -1,
                "Name": "Sprint Qualifying",
                "StartDate": relocate_tz(
                    to_datetime(meeting.sprint_qualifying.date + "T" + meeting.sprint_qualifying.time),
                    source_tz = "UTC",
                    target_location = meeting.circuit.location.country).strftime("%Y-%m-%dT%H:%M:%S")
            })
        new_meeting["Sessions"].append({
            "Key": "J" + meeting.round + "R",
            "Type": "Race",
            "Name": "Race",
            "StartDate": relocate_tz(
                to_datetime(meeting.date + "T" + (meeting.time or "00:00:00")),
                source_tz = "UTC",
                target_location = meeting.circuit.location.country).strftime("%Y-%m-%dT%H:%M:%S")
        })

        circuit_dict = meeting.circuit.to_dict()
        circuit_dict["ShortName"] = circuit_dict.get("circuitId", None)

        new_meeting["Key"] = "J" + meeting.round
        new_meeting["round"] = meeting.round
        new_meeting["url"]  = meeting.url
        new_meeting["Circuit"] = circuit_dict
        new_meeting["Location"] = meeting.circuit.location.locality
        new_meeting["Code"] = "F1" + str(meeting.season) + f"{int(meeting.round):02d}"
        new_meeting["OfficialName"] = None
        new_meeting["Country"] = {"name":meeting.circuit.location.country}
        new_meeting["Name"] = meeting.race_name
        new_meeting["Number"] = meeting.round
        all_meetings.append(new_meeting)
    return all_meetings


def _norm_schedule_str(value: object | None) -> str:
    if value is None:
        return ""
    return str(value).strip().casefold()


def fetch_jolpica_season_races_list(season_identifier: int) -> tuple[list, bool]:
    """Return ``(races, success)`` from Jolpica ``get_races`` only."""
    try:
        races = jolpica_client.query().season(season_identifier).get_races().data.races
        return (list(races) if races is not None else []), True
    except Exception:
        return [], False


def jolpica_season_races_fetch_ok(season_identifier: int) -> bool:
    """
    True if Jolpica ``get_races`` for the calendar year completes without error.

    Does not require a non-empty race list (API reachability / valid season query).
    """
    _, ok = fetch_jolpica_season_races_list(season_identifier)
    return ok


def livetiming_meeting_in_season_index(payload: dict, meeting_name: str) -> bool:
    """True if a Livetiming season ``Index.json`` payload lists the meeting by ``Name``."""
    if payload is None or not isinstance(payload, dict):
        return False
    target = _norm_schedule_str(meeting_name)
    if not target:
        return False
    meetings = payload.get("Meetings")
    if not meetings:
        return False
    if isinstance(meetings, dict):
        iterable = meetings.values()
    else:
        iterable = meetings
    for m in iterable:
        if _norm_schedule_str(m.get("Name")) == target:
            return True
    return False


def livetiming_session_in_season_index(
    payload: dict,
    meeting_name: str,
    session_name: str | None,
    session_type: str | None,
    session_number: int | None,
) -> bool:
    """
    True if the season index lists the session under the given meeting ``Name``.

    Matches ``Sessions`` entries by ``Name`` first, else by ``Type`` and ``Number``
    (aligned with :func:`merge_meetings` / season table session_type rules).
    """
    if not livetiming_meeting_in_season_index(payload, meeting_name):
        return False
    m_target = _norm_schedule_str(meeting_name)
    meeting_obj = None
    meetings = payload.get("Meetings")
    if isinstance(meetings, dict):
        iterable = meetings.values()
    else:
        iterable = meetings or []
    for m in iterable:
        if _norm_schedule_str(m.get("Name")) == m_target:
            meeting_obj = m
            break
    if meeting_obj is None:
        return False

    sn_target = _norm_schedule_str(session_name)
    st_target = _norm_schedule_str(session_type)

    for sess in meeting_obj.get("Sessions") or []:
        if sn_target and _norm_schedule_str(sess.get("Name")) == sn_target:
            return True
        st = _norm_schedule_str(sess.get("Type"))
        if not st_target or st != st_target:
            continue
        if "Number" in sess:
            if sess.get("Number") != session_number:
                continue
        return True
        # return session_number is None
    return False


def jolpica_meeting_in_races(races: list, meeting_name: str) -> bool:
    """True if any Jolpica race's ``race_name`` matches ``meeting_name`` (case-insensitive)."""
    target = _norm_schedule_str(meeting_name)
    if not target or not races:
        return False
    for race in races:
        rn = _norm_schedule_str(getattr(race, "race_name", None))
        if rn == target:
            return True
    return False


def _jolpica_race_dict(race: object) -> dict:
    if hasattr(race, "to_dict"):
        return race.to_dict()
    return dict(race) if isinstance(race, dict) else {}


def jolpica_find_race_for_meeting(races: list, meeting_name: str) -> object | None:
    target = _norm_schedule_str(meeting_name)
    if not target:
        return None
    for race in races or []:
        if _norm_schedule_str(getattr(race, "race_name", None)) == target:
            return race
    return None


def jolpica_session_available_on_race(
    race: object,
    session_name: str | None,
    session_type: str | None,
    session_number: int | None,
) -> bool:
    """
    Whether Jolpica exposes timing/date fields for this session on the given race row.

    Mirrors key presence used in :func:`merge_meetings` (``FirstPractice``, ``Sprint``, etc.).
    The main grand prix ``Race`` is always considered present when the race row exists.
    """
    d = _jolpica_race_dict(race)
    sn = _norm_schedule_str(session_name)
    st = _norm_schedule_str(session_type)
    num = session_number

    if sn == "race" or (st == "race" and num != -1):
        return True
    if sn == "sprint" or (st == "race" and num == -1):
        return "Sprint" in d
    if "sprint" in sn and "qualifying" in sn:
        return "SprintQualifying" in d
    if st == "qualifying" and num == -1:
        return "SprintQualifying" in d
    if sn == "qualifying" or st == "qualifying":
        return "Qualifying" in d

    practice_key = None
    if sn in ("practice 1", "fp1"):
        practice_key = "FirstPractice"
    elif sn in ("practice 2", "fp2"):
        practice_key = "SecondPractice"
    elif sn in ("practice 3", "fp3"):
        practice_key = "ThirdPractice"
    elif st == "practice" and num == 1:
        practice_key = "FirstPractice"
    elif st == "practice" and num == 2:
        practice_key = "SecondPractice"
    elif st == "practice" and num == 3:
        practice_key = "ThirdPractice"
    if practice_key:
        return practice_key in d

    return False


def fetch_livetiming_season_index(season_identifier: int) -> tuple[dict, bool]:
    """
    Fetch Livetiming season ``Index.json`` for a calendar year.

    Returns
    -------
    tuple[dict, bool]
        ``(payload, success)``. On failure, ``payload`` is ``{}`` and ``success`` is False.
    """
    try:
        data = livetimingF1_request(urljoin(str(season_identifier) + "/", "Index.json"))
        return data, True
    except Exception:
        return {}, False


def fetch_jolpica_season_meetings(season_identifier: int) -> tuple[list, bool, object | None]:
    """
    Fetch Jolpica season list entry and races for a calendar year.

    Returns
    -------
    tuple[list, bool, object | None]
        ``(races, success, season_row)`` where ``season_row`` is the matching season
        metadata (for wiki URL) or ``None``.
    """
    races, races_ok = fetch_jolpica_season_races_list(season_identifier)
    if not races_ok:
        return [], False, None
    try:
        seasons_data_jolpica = next(
            (
                season
                for season in jolpica_client.get_seasons(limit=100).data.seasons
                if int(season.season) == season_identifier
            ),
            None,
        )
        is_jolpica_available = bool(seasons_data_jolpica)
        return races, is_jolpica_available, seasons_data_jolpica
    except Exception:
        return races, False, None


def fetch_livetiming_session_index(full_path: str) -> tuple[dict, bool]:
    """
    Fetch Livetiming session ``Index.json`` (feeds manifest) for a built session URL path.

    Returns
    -------
    tuple[dict, bool]
        ``(payload, success)``. On failure, ``payload`` is ``{}`` and ``success`` is False.
    """
    try:
        data = livetimingF1_request(urljoin(full_path, "Index.json"))
        return data, True
    except Exception:
        return {}, False


def download_season_data(season_identifier: int):
    """
    Downloads and filters F1 data based on the provided season identifier.
    Parameters
    ----------
    season_identifier : :class:`int`
        The unique identifier for the F1 season.

    Returns
    ----------
    dict
        The filtered dataset containing the requested season data.
    """

    season_data_livetiming, is_livetiming_available = fetch_livetiming_season_index(season_identifier)
    season_races, is_jolpica_available, seasons_data_jolpica = fetch_jolpica_season_meetings(
        season_identifier
    )

    if not is_jolpica_available and not is_livetiming_available:
        raise livef1Exception("No data available for the season.")

    if is_livetiming_available:
        meetings_livetiming = season_data_livetiming["Meetings"]
    else: meetings_livetiming = {}
    if is_jolpica_available: meetings_jolpica = season_races
    else: meetings_jolpica = {}

    all_meetings = merge_meetings(meetings_livetiming, meetings_jolpica)

    season_data = {
        "is_livetiming_available": is_livetiming_available,
        "is_jolpica_available": is_jolpica_available,
        "wiki": seasons_data_jolpica.url if seasons_data_jolpica else None,
        "season": seasons_data_jolpica.season if seasons_data_jolpica else None,
        **season_data_livetiming,
        "Meetings": all_meetings,
        "livetiming_data": season_data_livetiming,
        "jolpica_data": season_races
    }

    return season_data


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
        season_data = download_season_data(season_identifier)
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
