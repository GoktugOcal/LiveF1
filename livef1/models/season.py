# Standard Library Imports
import urllib
import json
import dateutil
import sys

# Third-Party Library Imports
import pandas as pd
# Internal Project Imports
from ..adapters import download_data
from ..adapters.functions import fetch_livetiming_season_index, jolpica_season_races_fetch_ok
from ..adapters.jolpicaf1_adapter import jolpica_client
from ..adapters.other import parse_schedule_from_f1com

from .driver import Driver, _jolpica_driver_dict
from .constructor import Constructor, _jolpica_constructor_dict
from ..models.meeting import Meeting

from ..utils.helper import json_parser_for_objects, build_session_endpoint
from ..utils.logger import logger
from ..utils.constants import SESSIONS_COLUMN_MAP

from ..data_processing.jolpica_etl import parse_driver_standings, parse_constructor_standings


class Season:
    """
    Represents a Formula 1 season, containing methods to load and manage the season's meetings and sessions.

    Attributes
    ----------
    year : :class:`int`
        The year of the season.
    meetings : list of :class:`~Meeting`
        A list of :class:`Meeting` objects for the season.
    drivers : dict
        Jolpica drivers keyed by permanent number or driver id.
    constructors : dict
        Jolpica constructors keyed by ``constructorId``.
    driverStandings : list of dict
        Parsed season cumulative driver standings.
    constructorStandings : list of dict
        Parsed season cumulative constructor standings.
    """

    def __init__(
        self,
        year=None,
        meetings=None,
        season=None,
        wiki=None,
        livetiming_data: dict = None,
        jolpica_data: dict = None,
        is_livetiming_available=None,
        is_jolpica_available=None,
        **kwargs
    ):
        """
        Initializes the Season object with the given year and meetings.

        Parameters
        ----------
        year : :class:`int`
            The year of the season.
        meetings : list
            Raw meetings data to initialize the season.
        """

        self.year = year or season
        self.meetings_json = meetings
        self.is_livetiming_available = is_livetiming_available
        self.is_jolpica_available = is_jolpica_available
        self.wiki = wiki
        self.drivers = []
        self.constructors = {}
        self.livetiming_data = livetiming_data
        self.jolpica_data = jolpica_data
        self.load()  # Load the data for the season upon initialization.

    def _check_if_jolpica_available(self):
        """
        Checks if Jolpica ``get_races`` succeeds for this season year.
        """
        self.is_jolpica_available = jolpica_season_races_fetch_ok(self.year)
        return self.is_jolpica_available

    def _check_if_livetiming_available(self):
        """
        Checks if the Livetiming API is available for the season.
        """
        _, ok = fetch_livetiming_season_index(self.year)
        self.is_livetiming_available = ok
        return self.is_livetiming_available

    def load(self):
        """
        Loads the season data from the API and populates the `meetings` attribute.
        """
        # self.meetings_json = self.meetings  # Store raw meeting data.
        self.meetings = []  # Initialize meetings list.

        self.parse_sessions()  # Parse sessions from the meetings.
        self.set_meetings()  # Create Meeting objects for each meeting.
        self._load_drivers()
        self._load_constructors()
        self._load_driver_standings()
        self._load_constructor_standings()
    
    def _load_drivers(self):
        """
        Loads the drivers data from the API and populates the `drivers` attribute.
        """
        drivers_jolpica = jolpica_client.query().season(self.year).get_drivers(limit=100).data.drivers
        self.drivers = {}
        for driver in drivers_jolpica:
            if driver.permanent_number is not None:
                driver_dict = _jolpica_driver_dict(driver.to_dict())
            else:
                driver_dict = _jolpica_driver_dict(driver.to_dict())
            self.drivers[driver.permanent_number or driver.driver_id] = Driver(**driver_dict)

    def _load_constructors(self):
        """
        Loads constructors from Jolpica and populates ``constructors`` keyed by ``constructorId``.
        """
        constructors_jolpica = jolpica_client.query().season(self.year).get_constructors(limit=100).data.constructors
        self.constructors = {}
        for c in constructors_jolpica:
            d = c.to_dict()
            cid = d.get("constructorId")
            if cid is None:
                continue
            self.constructors[cid] = Constructor(**_jolpica_constructor_dict(d))
    
    def _load_driver_standings(self):
        driver_standings = jolpica_client.query().season(self.year).get_driver_standings(limit=100).data.standings_lists[0].to_dict()["DriverStandings"]
        self.driverStandings = parse_driver_standings(self, driver_standings)
        logger.info(f"Driver standings have been loaded and saved to 'season.driverStandings'.")

    def _load_constructor_standings(self):
        ctor_standings = jolpica_client.query().season(self.year).get_constructor_standings(limit=100).data.standings_lists[0].to_dict()["ConstructorStandings"]
        self.constructorStandings = parse_constructor_standings(self, ctor_standings)
        logger.info("Constructor standings have been loaded and saved to 'season.constructorStandings'.")
    
    def get_driver(self, identifier: str) -> Driver:
        """
        Get a specific driver by their number, name, or short name.

        Parameters
        ----------
        identifier : str
            The driver's racing number, full name, or short name.

        Returns
        -------
        Driver
            The Driver object for the specified identifier, or None if not found.
        """
        for driver in self.drivers.values():
            if (
                str(driver.RacingNumber) == identifier or
                driver.FirstName.lower() == identifier.lower() or
                driver.LastName.lower() == identifier.lower() or
                driver.Tla.lower() == identifier.lower()
            ):
                return driver
        return None

    def get_constructor(self, identifier: str) -> Constructor:
        """
        Get a constructor by ``constructorId`` or by case-insensitive name match.
        """
        if identifier is None:
            return None
        for constructor in self.constructors.values():
            if constructor.id == identifier or (
                constructor.Name and constructor.Name.lower() == identifier.lower()
            ):
                return constructor
        return None

    def set_meetings(self):
        """
        Creates :class:`~Meeting` objects for each meeting in the `meetings_json` attribute
        and adds them to the `meetings` list.
        """
        self.meetings = []  # Reset meetings list.
        
        # Iterate through each meeting in the raw meeting data.
        for meeting in self.meetings_json:
            self.meetings.append(
                Meeting(
                    season=self,
                    loaded=True,
                    **json_parser_for_objects(meeting)  # Unpack the meeting data into the Meeting object.
                )
            )

    def parse_sessions(self):
        """
        Parses session data from the meetings and organizes it into a DataFrame.

        The resulting DataFrame is stored in the `meetings_table` attribute, indexed by
        `season_year`, `meeting_location`, and `session_type`.
        """
        session_all_data = []  # List to hold all session data.

        # Iterate through each meeting in the meetings_json attribute.
        for meeting in self.meetings_json:
            for session in meeting["Sessions"]:  # Iterate through each session in the meeting.
                session_data = {
                    "season_year": dateutil.parser.parse(session["StartDate"]).year,
                    "meeting_code": meeting["Code"],
                    "meeting_key": meeting.get("Key", None),
                    "round": meeting.get("round", None),
                    "meeting_number": meeting.get("Number", None),
                    "meeting_location": meeting.get("Location", None),
                    "meeting_offname": meeting.get("OfficialName", None),
                    "meeting_name": meeting.get("Name", None),
                    "meeting_country_key": meeting.get("Country", {}).get("Key", None),
                    "meeting_country_code": meeting.get("Country", {}).get("Code", None),
                    "meeting_country_name": meeting.get("Country", {}).get("Name", meeting.get("Circuit", {}).get("Location", {}).get("Country", None)),
                    "meeting_circuit_key": meeting.get("Circuit", {}).get("Key", None),
                    "meeting_circuit_shortname": meeting.get("Circuit", {}).get("ShortName", None),
                    "session_key": session.get("Key", None),
                    "session_type": session["Type"] + " " + str(session["Number"]) if "Number" in session else session["Type"],
                    "session_name": session.get("Name", None),
                    "session_startDate": session.get("StartDate", None),
                    "session_endDate": session.get("EndDate", None),
                    "gmtoffset": session.get("GmtOffset", None),
                    "path": session.get("Path", None),
                }
                session_all_data.append(session_data)  # Add the session data to the list.

        # Create a DataFrame to organize the sessions data.
        self.season_table = pd.DataFrame(session_all_data)
        self.season_table["meeting_key"] = self.season_table["meeting_key"].fillna(-1)
        self.season_table = self.season_table.set_index(["meeting_key"])
        self.season_table["session_startDate"] = pd.to_datetime(self.season_table["session_startDate"], format="ISO8601")
        self.season_table["session_endDate"] = pd.to_datetime(self.season_table["session_endDate"], format="ISO8601")
        self.season_table = self.season_table.sort_values("session_startDate")

        self.meetings_table = self.season_table \
            .groupby(["meeting_key","meeting_name"]) \
            .agg(
                {
                    "round": "first",
                    "meeting_code": "first",
                    # "meeting_name": "first",
                    "meeting_offname": "first",
                    "meeting_circuit_shortname": "first",
                    "session_name": "count",
                    "session_startDate": "max"
                }
            ) \
            .sort_values("session_startDate") \
            .reset_index() \
            .rename(
                columns = {
                    **SESSIONS_COLUMN_MAP,
                    **{
                        "session_startDate" : "Race Startdate",
                        "session_name" : "No. Sessions"
                    }
                }
            )

        self.season_table = self.season_table.rename(columns = SESSIONS_COLUMN_MAP)

    def get_schedule(self):
        self.schedule = parse_schedule_from_f1com(self.year)  # Parse the schedule from F1.com for the season.
        return self.schedule

    def __repr__(self):
        """
        Returns a string representation of the `meetings_table` for display.
        """
        if "IPython" not in sys.modules:
            # definitely not in IPython
            return self.__str__() # Print the meetings table.
        else:
            display(self.season_table) # Display the meetings table.
            # return self.__str__()
            return ""

    def __str__(self):
        """
        Returns a string representation of the `meetings_table` for easy reading.
        """
        return self.season_table.__str__()  # Return the string representation of the meetings table.
