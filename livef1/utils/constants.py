# Default API URL and endpoints
BASE_URL = "https://livetiming.formula1.com"
STATIC_ENDPOINT = "/static/"
SIGNALR_ENDPOINT = "/signalr/"

DEFAULT_METHOD = "livef1"

REALTIME_CALLBACK_DEFAULT_PARAMETERS = [
  # "topic_name",
  # "data",
  # "timestamp"
  "records"
]

QUERY_STOPWORDS = [
    "formula",
    "1",
    "grand",
    "prix"
]

SESSIONS_COLUMN_MAP = {
    'season_year': 'Season Year',
    'meeting_code': 'Meeting Code',
    'meeting_key': 'Meeting Key',
    'meeting_number': 'Meeting Number',
    'meeting_location': 'Meeting Location',
    'meeting_offname': 'Meeting Offname',
    'meeting_name': 'Meeting Name',
    'meeting_country_key': 'Meeting Country Key',
    'meeting_country_code': 'Meeting Country Code',
    'meeting_country_name': 'Meeting Country Name',
    'meeting_circuit_key': 'Meeting Circuit Key',
    'meeting_circuit_shortname': 'Meeting Circuit Shortname',
    'session_key': 'Session Key',
    'session_type': 'Session Type',
    'session_name': 'Session Name',
    'session_startDate': 'Session Startdate',
    'session_endDate': 'Session Enddate',
    'gmtoffset': 'Gmtoffset',
    'path': 'Path'
}

EXCLUDED_COLUMNS_FOR_SEARCH_SUGGESTION = ["meeting_offname"]

session_index = {
  "Feeds": {
    "SessionInfo": {
      "KeyFramePath": "SessionInfo.json",
      "StreamPath": "SessionInfo.jsonStream"
    },
    "ArchiveStatus": {
      "KeyFramePath": "ArchiveStatus.json",
      "StreamPath": "ArchiveStatus.jsonStream"
    },
    "TrackStatus": {
      "KeyFramePath": "TrackStatus.json",
      "StreamPath": "TrackStatus.jsonStream"
    },
    "SessionData": {
      "KeyFramePath": "SessionData.json",
      "StreamPath": "SessionData.jsonStream"
    },
    "ContentStreams": {
      "KeyFramePath": "ContentStreams.json",
      "StreamPath": "ContentStreams.jsonStream"
    },
    "AudioStreams": {
      "KeyFramePath": "AudioStreams.json",
      "StreamPath": "AudioStreams.jsonStream"
    },
    "ExtrapolatedClock": {
      "KeyFramePath": "ExtrapolatedClock.json",
      "StreamPath": "ExtrapolatedClock.jsonStream"
    },
    "TyreStintSeries": {
      "KeyFramePath": "TyreStintSeries.json",
      "StreamPath": "TyreStintSeries.jsonStream"
    },
    "SessionStatus": {
      "KeyFramePath": "SessionStatus.json",
      "StreamPath": "SessionStatus.jsonStream"
    },
    "TimingDataF1": {
      "KeyFramePath": "TimingDataF1.json",
      "StreamPath": "TimingDataF1.jsonStream"
    },
    "TimingData": {
      "KeyFramePath": "TimingData.json",
      "StreamPath": "TimingData.jsonStream"
    },
    "DriverList": {
      "KeyFramePath": "DriverList.json",
      "StreamPath": "DriverList.jsonStream"
    },
    "LapSeries": {
      "KeyFramePath": "LapSeries.json",
      "StreamPath": "LapSeries.jsonStream"
    },
    "TopThree": {
      "KeyFramePath": "TopThree.json",
      "StreamPath": "TopThree.jsonStream"
    },
    "TimingAppData": {
      "KeyFramePath": "TimingAppData.json",
      "StreamPath": "TimingAppData.jsonStream"
    },
    "TimingStats": {
      "KeyFramePath": "TimingStats.json",
      "StreamPath": "TimingStats.jsonStream"
    },
    "Heartbeat": {
      "KeyFramePath": "Heartbeat.json",
      "StreamPath": "Heartbeat.jsonStream"
    },
    "WeatherData": {
      "KeyFramePath": "WeatherData.json",
      "StreamPath": "WeatherData.jsonStream"
    },
    "WeatherDataSeries": {
      "KeyFramePath": "WeatherDataSeries.json",
      "StreamPath": "WeatherDataSeries.jsonStream"
    },
    "Position.z": {
      "KeyFramePath": "Position.z.json",
      "StreamPath": "Position.z.jsonStream"
    },
    "CarData.z": {
      "KeyFramePath": "CarData.z.json",
      "StreamPath": "CarData.z.jsonStream"
    },
    "TlaRcm": {
      "KeyFramePath": "TlaRcm.json",
      "StreamPath": "TlaRcm.jsonStream"
    },
    "RaceControlMessages": {
      "KeyFramePath": "RaceControlMessages.json",
      "StreamPath": "RaceControlMessages.jsonStream"
    },
    "PitLaneTimeCollection": {
      "KeyFramePath": "PitLaneTimeCollection.json",
      "StreamPath": "PitLaneTimeCollection.jsonStream"
    },
    "CurrentTyres": {
      "KeyFramePath": "CurrentTyres.json",
      "StreamPath": "CurrentTyres.jsonStream"
    },
    "TeamRadio": {
      "KeyFramePath": "TeamRadio.json",
      "StreamPath": "TeamRadio.jsonStream"
    }
  }
}

TOPICS_MAP = {
  "SessionInfo": {
    "key": "Session_Info",
    "description": "Details about the current session.",
    "default_is_stream": True
  },
  "ArchiveStatus": {
    "key": "Archive_Status",
    "description": "Status of archived session data.",
    "default_is_stream": True
  },
  "TrackStatus": {
    "key": "Track_Status",
    "description": "Current conditions and status of the track.",
    "default_is_stream": True
  },
  "SessionData": {
    "key": "Session_Data",
    "description": "Raw data for the ongoing session.",
    "default_is_stream": True
  },
  "ContentStreams": {
    "key": "Content_Streams",
    "description": "Streams of multimedia content.",
    "default_is_stream": True
  },
  "AudioStreams": {
    "key": "Audio_Streams",
    "description": "Live audio broadcast streams.",
    "default_is_stream": True
  },
  "ExtrapolatedClock": {
    "key": "Extrapolated_Clock",
    "description": "Predicted session time data.",
    "default_is_stream": True
  },
  "TyreStintSeries": {
    "key": "Tyre_Stints",
    "description": "Data on tyre usage over stints.",
    "default_is_stream": True
  },
  "SessionStatus": {
    "key": "Session_Status",
    "description": "Live status of the session.",
    "default_is_stream": True
  },
  "TimingDataF1": {
    "key": "Timing_Data_F1",
    "description": "Timing information specific to Formula 1.",
    "default_is_stream": True
  },
  "TimingData": {
    "key": "Timing_Data",
    "description": "General timing data for the session.",
    "default_is_stream": True
  },
  "DriverList": {
    "key": "Driver_List",
    "description": "List of active drivers in the session.",
    "default_is_stream": False
  },
  "LapSeries": {
    "key": "Lap_Series",
    "description": "Data series for laps completed.",
    "default_is_stream": True
  },
  "TopThree": {
    "key": "Top_Three",
    "description": "Information about the top three drivers.",
    "default_is_stream": True
  },
  "TimingAppData": {
    "key": "Timing_App",
    "description": "Timing data from the application.",
    "default_is_stream": True
  },
  "TimingStats": {
    "key": "Timing_Stats",
    "description": "Statistical analysis of timing data.",
    "default_is_stream": True
  },
  "Heartbeat": {
    "key": "Heartbeat",
    "description": "Regular status signal of the system.",
    "default_is_stream": True
  },
  "WeatherData": {
    "key": "Weather_Data",
    "description": "Current weather information.",
    "default_is_stream": True
  },
  "WeatherDataSeries": {
    "key": "Weather_History",
    "description": "Historical weather data series.",
    "default_is_stream": True
  },
  "Position.z": {
    "key": "Position",
    "description": "Position data of cars.",
    "default_is_stream": True
  },
  "CarData.z": {
    "key": "Car_Data",
    "description": "Car sensor data.",
    "default_is_stream": True
  },
  "TlaRcm": {
    "key": "Team_Audio_RCM",
    "description": "Team live audio and race control messages.",
    "default_is_stream": True
  },
  "RaceControlMessages": {
    "key": "Race_Control",
    "description": "Messages from race control.",
    "default_is_stream": True
  },
  "PitLaneTimeCollection": {
    "key": "Pit_Lane_Times",
    "description": "Timing data for pit lane activity.",
    "default_is_stream": True
  },
  "CurrentTyres": {
    "key": "Current_Tyres",
    "description": "Details of the tyres currently in use.",
    "default_is_stream": True
  },
  "DriverRaceInfo": {
    "key": "Driver_Race_Info",
    "description": "Information about individual driver performance.",
    "default_is_stream": True
  },
  "TeamRadio": {
    "key": "Team_Radio",
    "description": "Radio communications with the team.",
    "default_is_stream": True
  },
  "ChampionshipPrediction": {
    "key": "Championship_Prediction",
    "description": "Predictions for championship outcomes.",
    "default_is_stream": True
  },
  "OvertakeSeries": {
    "key": "Overtake_Series",
    "description": "Data series tracking overtakes.",
    "default_is_stream": True
  },
  "DriverScore": {
    "key": "Driver_Score",
    "description": "Scores reflecting driver performance.",
    "default_is_stream": True
  },
  "SPFeed": {
    "key": "SP_Feed",
    "description": "Special data feed for the session.",
    "default_is_stream": True
  },
  "PitStopSeries": {
    "key": "Pit_Stop_Series",
    "description": "Data series for multiple pit stops.",
    "default_is_stream": True
  },
  "PitStop": {
    "key": "Pit_Stop",
    "description": "Details about individual pit stops.",
    "default_is_stream": True
  },
  "LapCount": {
    "key": "Lap_Count",
    "description": "Number of laps completed in the session.",
    "default_is_stream": True
  },
  "DriverTracker": {
    "key": "Driver_Tracker",
    "description": "Real-time tracking of driver positions.",
    "default_is_stream": True
  }
}

channel_name_map = {
  '0': 'rpm',
  '2': 'speed',
  '3': 'n_gear',
  '4': 'throttle',
  '5': 'brake',
  '45': 'drs'
}

interpolation_map = {
  #Position
  'status': 'ffill',
  'X': 'quadratic',
  'Y': 'quadratic',
  'Z': 'quadratic',
  #Car
  'speed': 'linear',
  'rpm': 'linear',
  'throttle': 'linear',
  'brake': 'ffill',
  'drs': 'ffill',
  'n_gear': 'ffill',
  #Weather
  "AirTemp" : "linear",
  "Humidity" : "linear",
  "Pressure" : "linear",
  "Rainfall" : "linear",
  "TrackTemp" : "linear",
  "WindDirection" : "linear",
  "WindDirection" : "linear",
  "WindSpeed" : "polynomial",
  }

SILVER_SESSION_TABLES = ["laps", "carTelemetry"]
# SILVER_SESSION_TABLES = ["laps", "car_telemetry", "weather", "timing"]

TABLE_GENERATION_FUNCTIONS = {
    "laps": "generate_laps_table",
    "carTelemetry": "generate_car_telemetry_table"
}

TABLE_REQUIREMENTS = {
    "laps": ["TimingData", "RaceControlMessages"],
    "carTelemetry": ["TimingData", "CarData.z", "Position.z", "SessionData"]
}
