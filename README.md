# LiveF1 - An Open-Source Formula 1 Data Processing Toolkit
LiveF1 is a powerful toolkit for accessing and analyzing Formula 1 data in real time or from historical archives, designed for developers, analysts, and fans building applications around F1 insights.

### What it is provided in LiveF1
- **Real-Time Race Data**: Provides live telemetry, timing, and position updates, ideal for powering dashboards and live analytics.
- **Historical Data Access**: Includes comprehensive race data from past seasons, perfect for performance analysis and comparisons.
- **Data Processing Modules**: Built-in ETL tools make raw data immediately usable, supporting analysis and seamless data storage.

In a nutshell:

**Using LiveF1, you can access real-time and historical racing data, making it easy to feed analytics and visualizations.**

## INSTALLATION
Please use `pip` to install livef1:
```bash
pip install livef1
```

It is simple. You are ready.

## USAGE

#### Import the library
```python
import livef1 as livef1
```

#### Get season object and its meetings + sessions
```python
season = livef1.get_season(
    season = 2024
)

print(season) # Shows the dataframe table of sessions and their informations
print(season.meetings) # Get meeting objects
```

#### Get meeting object and its sessions
```python
meeting = livef1.get_meeting(
    season = 2024,
    location = "Monza"
)

print(meeting) # Shows the dataframe table of sessions and their informations
print(meeting.sessions) # Get session objects
```

#### Get session object and load data
```python
session = livef1.get_session(
    season=2024,
    location="Monza",
    session="Race"
)

session.get_topic_names() # load /Info.json
print(session.topic_names_info)
```

```json
{
  "SessionInfo": {
    "KeyFramePath": "SessionInfo.json",
    "StreamPath": "SessionInfo.jsonStream"
  },
  "ArchiveStatus": {
    "KeyFramePath": "ArchiveStatus.json",
    "StreamPath": "ArchiveStatus.jsonStream"
  },
  "Position.z": {
    "KeyFramePath": "Position.z.json",
    "StreamPath": "Position.z.jsonStream"
  },
  "CarData.z": {
    .
    .
    .
```

Load specific data by name of data
```python
data = session.get_data(
    dataName = "Position.z",
    dataType = "StreamPath",
    stream = True
)

print(data)
#     SessionKey     timestamp                           Utc DriverNo   Status     X      Y     Z
# 0         9590  00:00:30.209  2024-09-01T12:08:13.7879709Z        1  OnTrack     0      0     0
# 1         9590  00:00:30.209  2024-09-01T12:08:13.7879709Z        3  OnTrack     0      0     0
# 2         9590  00:00:30.209  2024-09-01T12:08:13.7879709Z        4  OnTrack     0      0     0
# 3         9590  00:00:30.209  2024-09-01T12:08:13.7879709Z       10  OnTrack     0      0     0

```