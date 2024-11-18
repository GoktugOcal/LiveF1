# Standard Library Imports
import dateutil
import json

# Third-Party Library Imports
import pandas as pd
from typing import List, Dict

# Internal Project Imports
from ..api import download_data
from ..models.session import Session
from ..utils.helper import json_parser_for_objects, build_session_endpoint


class Meeting:
    """
    Represents a meeting in a specific season with relevant details and associated sessions.

    Attributes
    ----------
    season : :class:`season`
        The season this meeting belongs to.
    year : int
        The year of the meeting. :class:`season`
    code : int
        The unique code for the meeting.
    key : str
        The unique identifier for the meeting.
    number : int
        The sequential number of the meeting in the season.
    location : str
        The location (e.g., circuit name) of the meeting.
    officialname : str
        The official name of the meeting.
    name : str
        The name of the meeting.
    country : Dict
        Details about the country where the meeting takes place (e.g., key, code, name).
    circuit : Dict
        Details about the circuit where the meeting takes place (e.g., key, short name).
    sessions : List
        List of session objects associated with the meeting.
    loaded : bool
        Indicates whether the meeting data has been loaded.
    """

    def __init__(
        self,
        season: "Season" = None,
        year: int = None,
        code: int = None,
        key: str = None,
        number: int = None,
        location: str = None,
        officialname: str = None,
        name: str = None,
        country: Dict = None,
        circuit: Dict = None,
        sessions: List = None,
        loaded: bool = False,
        **kwargs  # In case new information comes from the API in future
    ):
        self.season = season
        self.loaded = loaded

        # Iterate over the kwargs and set them as attributes of the instance
        for key, value in locals().items():
            if value:
                setattr(self, key.lower(), value)

        if hasattr(self, "sessions"):
            self.sessions_json = self.sessions
            self.sessions = []
            self.set_sessions()

        self.parse_sessions()

    def load(self, force=False):
        """
        Load or reload meeting data from the API.

        .. note::
            Reloading is useful when updated data is required.

        Parameters
        ----------
        force : bool, optional
            If True, forces the reload of meeting data even if already loaded. Defaults to False.
        
        
        """
        if (not self.loaded) | (force):
            if force:
                print("Force load...")

            if hasattr(self, "year"):
                self.json_data = download_data(self.year, self.location)
            elif hasattr(self, "season"):
                self.json_data = download_data(self.season.year, self.location)

            for key, value in json_parser_for_objects(self.json_data).items():
                setattr(self, key.lower(), value)

            self.sessions_json = self.sessions
            self.sessions = []

            self.parse_sessions()
            self.set_sessions()
        else:
            print("The meeting has already been loaded. If you want to load anyway, use `force=True`.")

    def set_sessions(self):
        """
        Create session objects for the meeting using the session JSON data.

        .. note::
            This method populates the `sessions` attribute with `Session` objects derived from `sessions_json`.
        """
        for session_data in self.sessions_json:
            self.sessions.append(
                Session(
                    season=self.season,
                    meeting=self,
                    **json_parser_for_objects(session_data)
                )
            )

    def parse_sessions(self):
        """
        Parse session data to generate a detailed DataFrame of session metadata.

        .. note::
            The resulting DataFrame is stored in the `sessions_table` attribute and indexed by season year, meeting location, and session type.
        """
        session_all_data = []

        for session in self.sessions_json:
            session_data = {
                "season_year": dateutil.parser.parse(session["StartDate"]).year,
                "meeting_code": self.code,
                "meeting_key": self.key,
                "meeting_number": self.number,
                "meeting_location": self.location,
                "meeting_offname": self.officialname,
                "meeting_name": self.name,
                "meeting_country_key": self.country["Key"],
                "meeting_country_code": self.country["Code"],
                "meeting_country_name": self.country["Name"],
                "meeting_circuit_key": self.circuit["Key"],
                "meeting_circuit_shortname": self.circuit["ShortName"],
                "session_key": session.get("Key", None),
                "session_type": session["Type"] + " " + str(session["Number"]) if "Number" in session else session["Type"],
                "session_name": session.get("Name", None),
                "session_startDate": session.get("StartDate", None),
                "session_endDate": session.get("EndDate", None),
                "gmtoffset": session.get("GmtOffset", None),
                "path": session.get("Path", None),
            }
            session_all_data.append(session_data)

        self.sessions_table = pd.DataFrame(session_all_data).set_index(["season_year", "meeting_location", "session_type"])

    def __repr__(self):
        """
        Return a detailed string representation of the meeting.

        Returns
        -------
        str
            The string representation of the meeting's session table.
        """
        return self.sessions_table.__repr__()

    def __str__(self):
        """
        Return a readable string representation of the meeting.

        Returns
        -------
        str
            The string representation of the meeting's session table.
        """
        return self.sessions_table.__str__()