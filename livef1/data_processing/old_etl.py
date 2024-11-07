import json
import pandas as pd
from typing import (
    Optional,
    Union
)
from ..utils.helper import *

class livef1SessionETL:
    def __init__(self, session):
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
            'TimingData': parse_timing_data, # what is the difference with timingdataf1
            'LapSeries': parse_lap_series,
            'TopThree': parse_top_three,
            'TimingAppData': None,
            'TimingStats': parse_timing_data, # what is the difference with timingdataf1
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
            'DriverRaceInfo': parse_driver_race_info
            }

    def unified_parse(self, title, data):
        return self.function_map[title](
            data,
            self.session.key
            )

def parse_tyre_stint_series(
    data,
    sessionKey
    ):
    for key, value in data.items():
        for driver_no, stint in value["Stints"].items():
            if stint:
                for pit_count, current_info in stint.items():
                    record = {
                        **{
                            "session_key": sessionKey,
                            "timestamp": key,
                            "DriverNo": driver_no,
                            "PitCount": pit_count,
                        },
                        **current_info
                    }

                    yield record

def parse_driver_race_info(
    data,
    sessionKey
    ):
    for key, value in data.items():
        for driver_no, info in value.items():
            record = {
                **{
                    "session_key": sessionKey,
                    "timestamp": key,
                    "DriverNo": driver_no,
                },
                **info
            }
            
            yield record

def parse_current_tyres(
    data,
    sessionKey
    ):
    for key, value in data.items():
        for driver_no, info in value["Tyres"].items():
            record = {
                **{
                    "session_key": sessionKey,
                    "timestamp": key,
                    "DriverNo": driver_no,
                },
                **info
            }
            yield record

def parse_driver_list(
    data,
    sessionKey
    ):
    for driver_no, info in data.items():
        record = {
            **{ 
                "session_key" : sessionKey,
                "DriverNo": driver_no,
            },
            **info
        }
        
        yield record

def parse_session_data(
    data,
    sessionKey
    ):
    for key, value in data.items():
        for driver_no, info in value.items():
            try:
                record = {
                    **{
                        "session_key" : sessionKey
                    },
                    **list(info.values())[0]
                }
                
                yield record
            except Exception as e:
                pass

def parse_extrapolated_clock(
    data,
    sessionKey
    ):
    for key, info in data.items():
        record = {
            **{
                "session_key": sessionKey,
                "timestamp": key,
            },
            **info
        }
        yield record

def parse_timing_data(
    data,
    sessionKey
    ):
    def parse_helper(info, record, prefix=""):
        for info_k, info_v in info.items():
            if isinstance(info_v, list): record = {**record, **{**{info_k + "_" + str(sector_no+1) + "_" + k : v  for sector_no in range(len(info_v)) for k,v in info_v[sector_no].items()}}}
            elif isinstance(info_v, dict): record = parse_helper(info_v, record, prefix= prefix + info_k + "_")
            else: record = {**record, **{prefix + info_k : info_v}}
        return record

    for ts, value in data.items():
        if "Withheld" in value.keys(): withTheId = value["Withheld"]
        else: withTheId = None
        
        for driver_no, info in value["Lines"].items():
            record= {
                    "SessionKey" : sessionKey,
                    "timestamp" : ts,
                    "DriverNo" : driver_no
                }

            record = parse_helper(info, record)

            yield record

def parse_lap_series(
    data,
    sessionKey
    ):
    for ts, ts_value in data.items():
        for driver_no, driver_data in ts_value.items():
            if isinstance(driver_data["LapPosition"], list):
                for position in driver_data["LapPosition"]:
                    record = {
                            "SessionKey" : sessionKey,
                            "timestamp" : ts,
                            "DriverNo" : driver_no,
                            "Lap" : 0,
                            "LapPosition" : position
                        }
                    yield record
                
            
            elif isinstance(driver_data["LapPosition"], dict):
                for lap, position in driver_data["LapPosition"].items():
                    record = {
                            "SessionKey" : SessionKey,
                            "timestamp" : ts,
                            "DriverNo" : driver_no,
                            "Lap" : lap,
                            "LapPosition" : position
                        }
                    yield record

def parse_top_three(
    data,
    sessionKey
    ):
    for ts, ts_value in data.items():
        if "Withheld" in ts_value.keys():
            continue

        for position, info in ts_value["Lines"].items():

            record = {
                **{
                    "SessionKey" : sessionKey,
                    "timestamp" : ts,
                    "DriverAtPosition" : position
                },
                **info
            }
            yield record
    
def parse_session_status(
    data,
    sessionKey
    ):
    for ts, ts_value in data.items():
        record = {
            "SessionKey": sessionKey,
            "timestamp": ts,
            "status": ts_value["Status"]
        }
        yield record

def parse_hearthbeat(
    data,
    sessionKey
    ):
    for ts, ts_value in data.items():
        record = {
            "SessionKey": sessionKey,
            "timestamp": ts,
            "utc": ts_value["Utc"]
        }
        yield record

def parse_weather_data(
    data,
    sessionKey
    ):
    for ts, ts_value in data.items():
        record = {
            "SessionKey": sessionKey,
            "timestamp": ts
        }
        record = {
            **record,
            **ts_value
        }
        yield record

def parse_team_radio(
    data,
    sessionKey
    ):
    for ts, ts_value in data.items():
        record = {
                "SessionKey": 0,
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

def parse_tlarcm(
    data,
    sessionKey
    ):
    for ts, ts_value in data.items():
        record = {
                "SessionKey": 0,
                "timestamp": ts,
                "Message": ts_value["Message"]
            }
        
        yield record

def parse_race_control_messages(
    data,
    sessionKey
    ):
    for ts, ts_value in data.items():
        record = {
                "SessionKey": 0,
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


def parse_session_info(
    data,
    sessionKey
    ):
    for ts, value in data.items():
        if "Withheld" in value.keys(): withTheId = value["Withheld"]
        else: withTheId = None

        record= {
                "SessionKey" : sessionKey,
                "timestamp" : ts,
            }

        record = parse_helper_for_nested_dict(value, record)
        yield record


def parse_position_z(
    data,
    sessionKey
    ):
    for ts, v in data.items():
        parsed_entry = parse(v, zipped=True)
        for position_entry in parsed_entry["Position"]:
            utc = position_entry["Timestamp"]
            for driver_entry in position_entry["Entries"].items():
                
                record = {
                    **{
                        "SessionKey" : sessionKey,
                        "timestamp" : ts,
                        "Utc" : utc,
                        "DriverNo" : driver_entry[0]
                    },
                    **driver_entry[1]
                    }
                
                yield record

def parse_car_data_z(
    data,
    sessionKey
    ):
    for ts, v in data.items():
        parsed_entry = parse(v, zipped=True)
        for entry in parsed_entry["Entries"]:
            utc = entry["Utc"]
            for driver_entry in entry["Cars"].items():
                
                record = {
                    **{
                        "SessionKey" : sessionKey,
                        "timestamp" : ts,
                        "Utc" : utc,
                        "DriverNo" : driver_entry[0]
                    },
                    **driver_entry[1]["Channels"]
                    }
                
                yield record