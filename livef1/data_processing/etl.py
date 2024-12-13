# Standard Library Imports
import json

# Third-Party Library Imports
import pandas as pd
from typing import Optional, Union

# Internal Project Imports
from ..utils.helper import *
from ..utils.exceptions import (
    MissingFunctionError
)
from .parse_functions import *

# function_map = 

class livef1SessionETL:
    """
    A class that handles Extract-Transform-Load (ETL) operations for F1 session data.

    Parameters
    ----------
        session : :class:`~Session`
            The session object.

    Attributes
    ----------
        session : :class:`~Session`
            The session object containing session-related information.
        function_map :class:`dict`
            A dictionary mapping various session data titles to their corresponding parsing functions.
    """

    def __init__(self, session):
        """
        Initializes the livef1SessionETL class with a session object and function map.    
        """
        self.session = session
        self.function_map = function_map

    def unified_parse(self, title, data):
        """
        Unified parsing function that selects the appropriate parser function based on the title.
        
        Parameters
        ----------
            title : :class:`str`
                The title of the data to be parsed.
            data : :class:`dict`
                The session data to be parsed.
        
        Returns
        ----------
            Parsed data from the respective function in the function map.
        """
        if title not in self.function_map:
            logger.error(f"No parser function found for title: {title}")
            raise MissingFunctionError(f"No parser function available for title: {title}")
        
        try:
            # Perform the parsing
            logger.debug(f"Using parser function for title: {title}")
            parsed_data = self.function_map[title](data, self.session.key)
            logger.debug(f"Parsing successful for title: {title}")
            return parsed_data
        except Exception as e:
            logger.error("Parsing failed.")
            raise ETLError(f"Parser of {title} failed.")

# Parsing functions
function_map = {
    'SessionInfo': parse_session_info,
    'ArchiveStatus': None,
    'TrackStatus': parse_session_info,
    'SessionData': parse_session_data,
    'ContentStreams': None,
    'AudioStreams': None,
    'ExtrapolatedClock': parse_extrapolated_clock,
    'DriverList': parse_driver_list,
    'TimingDataF1': parse_timing_data,
    'TimingData': parse_timing_data,  # Potential duplicate with TimingDataF1
    'LapSeries': parse_lap_series,
    'TopThree': parse_top_three,
    'TimingAppData': None,
    'TimingStats': parse_timing_data,  # Same function used as TimingData
    'SessionStatus': parse_session_status,
    'TyreStintSeries': parse_tyre_stint_series,
    'Heartbeat': parse_hearthbeat,
    'Position.z': parse_position_z,
    'WeatherData': parse_weather_data,
    'WeatherDataSeries': None,
    'CarData.z': parse_car_data_z,
    'TeamRadio': parse_team_radio,
    'TlaRcm': parse_tlarcm,
    'RaceControlMessages': parse_race_control_messages,
    'PitLaneTimeCollection': None,
    'CurrentTyres': parse_current_tyres,
    'DriverRaceInfo': parse_driver_race_info,
    'ChampionshipPrediction': None,
    'OvertakeSeries': None,
    'DriverScore': None,
    'SPFeed': None,
    'PitStopSeries': None,
    'PitStop': None,
    'LapCount': None
}