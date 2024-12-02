# Default API URL and endpoints
BASE_URL = "https://livetiming.formula1.com"
STATIC_ENDPOINT = "/static/"
SIGNALR_ENDPOINT = "/signalr/"

DEFAULT_METHOD = "livef1"

REALTIME_CALLBACK_DEFAULT_PARAMETERS = [
  "topic_name",
  "data",
  "timestamp"
]

QUERY_STOPWORDS = [
    "formula",
    "1",
    "grand",
    "prix"
]

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