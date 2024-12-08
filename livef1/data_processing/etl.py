# Standard Library Imports
import json

# Third-Party Library Imports
import pandas as pd
from typing import Optional, Union

# Internal Project Imports
from ..utils.helper import *

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
        self.function_map = {
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
        return self.function_map[title](data, self.session.key)

# Parsing functions

def parse_tyre_stint_series(data, sessionKey):
    """
    Parses the tyre stint series data, generating records for each stint.

    Parameters
    ----------
        data : :class:`dict`
            The tyre stint series data.
        sessionKey : :class:`int`
            The key of the current session.
    
    Yields
    ----------
        dict :
            A record containing the session key, timestamp, driver number, pit count, and other stint-related info.
    """
    for key, value in data.items():
        for driver_no, stint in value["Stints"].items():
            if stint:
                for pit_count, current_info in stint.items():
                    record = {
                        "session_key": sessionKey,
                        "timestamp": key,
                        "DriverNo": driver_no,
                        "PitCount": pit_count,
                        **current_info
                    }
                    yield record

def parse_driver_race_info(data, sessionKey):
    """
    Parses driver race info data.

    Parameters
    ----------
        data : :class:`dict`
            The driver race info data.
        sessionKey : :class:`int`
            The key of the current session.
    
    Yields
    ----------
        dict :
            A record containing the session key, timestamp, driver number, and other race-related info.
    """
    for key, value in data.items():
        for driver_no, info in value.items():
            record = {
                "session_key": sessionKey,
                "timestamp": key,
                "DriverNo": driver_no,
                **info
            }
            yield record

def parse_current_tyres(data, sessionKey):
    """
    Parses current tyre data for each driver.

    Parameters
    ----------
        data : :class:`dict`
            The current tyre data.
        sessionKey : :class:`int`
            The key of the current session.
    
    Yields
    ----------
        dict :
            A record containing the session key, timestamp, driver number, and tyre-related info.
    """
    for key, value in data.items():
        for driver_no, info in value["Tyres"].items():
            record = {
                "session_key": sessionKey,
                "timestamp": key,
                "DriverNo": driver_no,
                **info
            }
            yield record

def parse_driver_list(data, sessionKey):
    """
    Parses the driver list data.

    Parameters
    ----------
        data : :class:`dict`
            The driver list data.
        sessionKey : :class:`int`
            The key of the current session.
    
    Yields
    ----------
        dict :
            A record containing the session key, driver number, and driver-related info.
    """
    for driver_no, info in data.items():
        record = {
            "session_key": sessionKey,
            "DriverNo": driver_no,
            **info
        }
        yield record

def parse_session_data(data, sessionKey):
    """
    Parses session data for each driver.

    Parameters
    ----------
        data : :class:`dict`
            The session data.
        sessionKey : :class:`int`
            The key of the current session.
    
    Yields
    ----------
        dict :
            A record containing the session key and session-related info.
    """
    for key, value in data.items():
        for driver_no, info in value.items():
            try:
                record = {
                    "session_key": sessionKey,
                    **list(info.values())[0]
                }
                yield record
            except Exception as e:
                pass

def parse_extrapolated_clock(data, sessionKey):
    """
    Parses extrapolated clock data.

    Parameters
    ----------
        data : :class:`dict`
            The extrapolated clock data.
        sessionKey : :class:`int`
            The key of the current session.

    Yields
    ----------
        dict :
            A record containing the session key, timestamp, and other clock-related info.
    """
    for key, info in data.items():
        record = {
            "session_key": sessionKey,
            "timestamp": key,
            **info
        }
        yield record

def parse_timing_data(data, sessionKey):
    """
    Parses timing data for each driver.

    Parameters
    ----------
        data : :class:`dict`
            The timing data.
        sessionKey : :class:`int`
            The key of the current session.

    Yields
    ----------
        dict :
            A record containing the session key, timestamp, driver number, and various timing metrics.
    """
    def parse_helper(info, record, prefix=""):
        """
        Recursively parses nested dictionaries in the timing data.
        """
        for info_k, info_v in info.items():
            if isinstance(info_v, list):
                record = {**record, **{f"{info_k}_{sector_no+1}_{k}": v for sector_no in range(len(info_v)) for k, v in info_v[sector_no].items()}}
            elif isinstance(info_v, dict):
                record = parse_helper(info_v, record, prefix=prefix + info_k + "_")
            else:
                record = {**record, **{prefix + info_k: info_v}}
        return record

    for ts, value in data.items():
        if "Withheld" in value.keys():
            withTheId = value["Withheld"]
        else:
            withTheId = None

        for driver_no, info in value["Lines"].items():
            record = {
                "SessionKey": sessionKey,
                "timestamp": ts,
                "DriverNo": driver_no
            }
            record = parse_helper(info, record)
            yield record

def parse_lap_series(data, sessionKey):
    """
    Parses lap series data for each driver.

    Parameters
    ----------
        data : :class:`dict`
            The lap series data.
        sessionKey : :class:`int`
            The key of the current session.

    Yields
    ----------
        dict :
            A record containing the session key, timestamp, driver number, lap number, and lap position.
    """
    for ts, ts_value in data.items():
        for driver_no, driver_data in ts_value.items():
            if isinstance(driver_data["LapPosition"], list):
                for position in driver_data["LapPosition"]:
                    record = {
                        "SessionKey": sessionKey,
                        "timestamp": ts,
                        "DriverNo": driver_no,
                        "Lap": 0,
                        "LapPosition": position
                    }
                    yield record
            elif isinstance(driver_data["LapPosition"], dict):
                for lap, position in driver_data["LapPosition"].items():
                    record = {
                        "SessionKey": sessionKey,
                        "timestamp": ts,
                        "DriverNo": driver_no,
                        "Lap": lap,
                        "LapPosition": position
                    }
                    yield record

def parse_top_three(data, sessionKey):
    """
    Parses the top three drivers' data.

    Parameters
    ----------
        data : :class:`dict`
            The top three data.
        sessionKey : :class:`int`
            The key of the current session.

    Yields
    ----------
        dict :
            A record containing the session key, timestamp, driver position, and related info.
    """
    for ts, ts_value in data.items():
        if "Withheld" in ts_value.keys():
            continue

        for position, info in ts_value["Lines"].items():
            record = {
                "SessionKey": sessionKey,
                "timestamp": ts,
                "DriverAtPosition": position,
                **info
            }
            yield record

def parse_session_status(data, sessionKey):
    """
    Parses the session status data.

    Parameters
    ----------
        data : :class:`dict`
            The session status data.
        sessionKey : :class:`int`
            The key of the current session.

    Yields
    ----------
        dict :
            A record containing the session key, timestamp, and session status.
    """
    for ts, ts_value in data.items():
        record = {
            "SessionKey": sessionKey,
            "timestamp": ts,
            "status": ts_value["Status"]
        }
        yield record

def parse_hearthbeat(data, sessionKey):
    """
    Parses the heartbeat data.

    Parameters
    ----------
        data : :class:`dict`
            The heartbeat data.
        sessionKey : :class:`int`
            The key of the current session.

    Yields
    ----------
        dict :
            A record containing the session key, timestamp, and UTC time.
    """
    for ts, ts_value in data.items():
        record = {
            "SessionKey": sessionKey,
            "timestamp": ts,
            "utc": ts_value["Utc"]
        }
        yield record

def parse_weather_data(data, sessionKey):
    """
    Parses weather data for the session.

    Parameters
    ----------
        data : :class:`dict`
            The weather data.
        sessionKey : :class:`int`
            The key of the current session.

    Yields
    ----------
        dict :
            A record containing the session key, timestamp, and weather-related information.
    """
    for ts, ts_value in data.items():
        record = {
            "SessionKey": sessionKey,
            "timestamp": ts,
            **ts_value
        }
        yield record

def parse_team_radio(data, sessionKey):
    """
    Parses team radio data.

    Parameters
    ----------
        data : :class:`dict`
            The team radio data.
        sessionKey : :class:`int`
            The key of the current session.

    Yields
    ----------
        dict :
            A record containing the session key, timestamp, and captured radio messages.
    """
    for ts, ts_value in data.items():
        record = {
            "SessionKey": sessionKey,
            "timestamp": ts
        }

        if isinstance(ts_value["Captures"], list):
            for capture in ts_value["Captures"]:
                capture_record = {
                    **record,
                    **capture
                }
                yield capture_record
        elif isinstance(ts_value["Captures"], dict):
            for capture in ts_value["Captures"].values():
                capture_record = {
                    **record,
                    **capture
                }
                yield capture_record

def parse_tlarcm(data, sessionKey):
    """
    Parses TLA RCM (Track Location Allocation Race Control Messages) data.

    Parameters
    ----------
        data : :class:`dict`
            The TLA RCM data.
        sessionKey : :class:`int`
            The key of the current session.

    Yields
    ----------
        dict :
            A record containing the session key, timestamp, and the message content.
    """
    for ts, ts_value in data.items():
        record = {
            "SessionKey": sessionKey,
            "timestamp": ts,
            "Message": ts_value["Message"]
        }
        yield record

def parse_race_control_messages(data, sessionKey):
    """
    Parses race control messages.

    Parameters
    ----------
        data : :class:`dict`
            The race control messages data.
        sessionKey : :class:`int`
            The key of the current session.

    Yields
    ----------
        dict :
            A record containing the session key, timestamp, and message details.
    """
    for ts, ts_value in data.items():
        record = {
            "SessionKey": sessionKey,
            "timestamp": ts
        }

        if isinstance(ts_value["Messages"], list):
            for capture in ts_value["Messages"]:
                capture_record = {
                    **record,
                    **capture
                }
                yield capture_record
        elif isinstance(ts_value["Messages"], dict):
            for capture in ts_value["Messages"].values():
                capture_record = {
                    **record,
                    **capture
                }
                yield capture_record

def parse_session_info(data, sessionKey):
    """
    Parses general session information.

    Parameters
    ----------
        data : :class:`dict`
            The session information data.
        sessionKey : :class:`int`
            The key of the current session.

    Yields
    ----------
        dict :
            A record containing the session key, timestamp, and session-related information.
    """
    for ts, value in data.items():
        if "Withheld" in value.keys():
            withTheId = value["Withheld"]
        else:
            withTheId = None

        record = {
            "SessionKey": sessionKey,
            "timestamp": ts
        }

        record = parse_helper_for_nested_dict(value, record)
        yield record

def parse_position_z(data, sessionKey):
    """
    Parses driver position (z-axis) data.

    Parameters
    ----------
        data : :class:`dict`
            The driver position data.
        sessionKey : :class:`int`
            The key of the current session.

    Yields
    ----------
        dict :
            A record containing the session key, timestamp, UTC time, driver number, and z-axis position data.
    """
    for ts, v in data.items():
        parsed_entry = parse(v, zipped=True)
        for position_entry in parsed_entry["Position"]:
            utc = position_entry["Timestamp"]
            for driver_entry in position_entry["Entries"].items():
                record = {
                    "SessionKey": sessionKey,
                    "timestamp": ts,
                    "Utc": utc,
                    "DriverNo": driver_entry[0],
                    **driver_entry[1]
                }
                yield record

def parse_car_data_z(data, sessionKey):
    """
    Parses car data (z-axis) for each driver.

    Parameters
    ----------
        data : :class:`dict`
            The car data.
        sessionKey : :class:`int`
            The key of the current session.

    Yields
    ----------
        dict :
            A record containing the session key, timestamp, UTC time, driver number, and channel data.
    """
    
    if isinstance(data, dict):
        for ts, v in data.items():
            parsed_entry = parse(v, zipped=True)
            for entry in parsed_entry["Entries"]:
                utc = entry["Utc"]
                for driver_entry in entry["Cars"].items():
                    record = {
                        "SessionKey": sessionKey,
                        "timestamp": ts,
                        "Utc": utc,
                        "DriverNo": driver_entry[0],
                        **driver_entry[1]
                    }
                    yield record

    elif isinstance(data, str):
        parsed_entry = parse(data, zipped=True)
        for entry in parsed_entry["Entries"]:
            utc = entry["Utc"]
            for driver_entry in entry["Cars"].items():
                record = {
                    "SessionKey": sessionKey,
                    "timestamp": None,
                    "Utc": utc,
                    "DriverNo": driver_entry[0],
                    **driver_entry[1]
                }
                yield record