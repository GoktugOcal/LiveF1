# Standard Library Imports
import urllib
import json
import dateutil
import sys

# Third-Party Library Imports
import pandas as pd

# Internal Project Imports
from ..adapters import download_data
from ..models.meeting import Meeting
from ..utils.helper import json_parser_for_objects, build_session_endpoint
from ..utils.constants import SESSIONS_COLUMN_MAP


class Season:
    """
    Represents a Formula 1 season, containing methods to load and manage the season's meetings and sessions.

    Attributes
    ----------
    year : :class:`int`
        The year of the season.
    meetings : list of :class:`~Meeting`
        A list of :class:`Meeting` objects for the season.
    """

    def __init__(self, year, meetings):
        """
        Initializes the Season object with the given year and meetings.

        Parameters
        ----------
        year : :class:`int`
            The year of the season.
        meetings : list
            Raw meetings data to initialize the season.
        """

        self.year = year
        self.load()  # Load the data for the season upon initialization.

    def load(self):
        """
        Loads the season data from the API and populates the `meetings` attribute.
        """
        self.json_data = download_data(self.year)  # Download data for the specified year.
        
        # Set attributes from the downloaded data using a helper function.
        for key, value in json_parser_for_objects(self.json_data).items():
            setattr(self, key.lower(), value)
        
        self.meetings_json = self.meetings  # Store raw meeting data.
        self.meetings = []  # Initialize meetings list.

        self.parse_sessions()  # Parse sessions from the meetings.
        self.set_meetings()  # Create Meeting objects for each meeting.

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
                    "meeting_key": meeting["Key"],
                    "meeting_number": meeting["Number"],
                    "meeting_location": meeting["Location"],
                    "meeting_offname": meeting["OfficialName"],
                    "meeting_name": meeting["Name"],
                    "meeting_country_key": meeting["Country"]["Key"],
                    "meeting_country_code": meeting["Country"]["Code"],
                    "meeting_country_name": meeting["Country"]["Name"],
                    "meeting_circuit_key": meeting["Circuit"]["Key"],
                    "meeting_circuit_shortname": meeting["Circuit"]["ShortName"],
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
        self.season_table = pd.DataFrame(session_all_data).set_index(["meeting_key"])
        self.season_table["session_startDate"] = pd.to_datetime(self.season_table["session_startDate"])
        self.season_table["session_endDate"] = pd.to_datetime(self.season_table["session_endDate"])

        self.meetings_table = self.season_table \
            .groupby("meeting_key") \
            .agg(
                {
                    "meeting_code": "first",
                    "meeting_name": "first",
                    "meeting_circuit_shortname": "first",
                    "session_name": "count"
                }
            ) \
            .join(
                self.season_table[self.season_table["session_type"] == "Race"]["session_startDate"]
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


    def __repr__(self):
        """
        Returns a string representation of the `meetings_table` for display.
        """
        if "IPython" not in sys.modules:
            # definitely not in IPython
            return self.__str__() # Print the meetings table.
        else:
            display(self.season_table) # Display the meetings table.
            return self.__str__()

    def __str__(self):
        """
        Returns a string representation of the `meetings_table` for easy reading.
        """
        return self.season_table.__str__()  # Return the string representation of the meetings table.
