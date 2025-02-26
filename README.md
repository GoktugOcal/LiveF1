# LiveF1 - An Open-Source Formula 1 Data Processing Toolkit

[![PyPI version](https://badge.fury.io/py/livef1.svg)](https://badge.fury.io/py/livef1)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

LiveF1 is a powerful Python toolkit for accessing and analyzing Formula 1 data in real-time or from historical archives. It's designed for developers, analysts, and F1 fans building applications around Formula 1 insights.

<p align="center">
  <img src="https://raw.githubusercontent.com/GoktugOcal/LiveF1/main/docs/source/_static/LiveF1Overview1.png" alt="LiveF1 Data Flow"/>
</p>

### Features
- **Real-Time Race Data**: Provides live telemetry, timing, and position updates, ideal for powering dashboards and live analytics.
- **Historical Data Access**: Includes comprehensive race data from past seasons, perfect for performance analysis and comparisons.
- **Data Processing Modules**: Built-in ETL tools make raw data immediately usable, supporting analysis and seamless data storage.
- **Easy Integration**: Simple API for both real-time and historical data

In a nutshell:

**Using LiveF1, you can access real-time and historical racing data, making it easy to feed analytics and visualizations.**

## Installation

Install using pip:

```bash
pip install livef1
```

## Quick Start

### Historical Data

Access data from past races:

```python
import livef1

# Get a specific race session
session = livef1.get_session(
    season=2024,
    meeting_identifier="Spa",
    session_identifier="Race"
)

# Load position data
position_data = session.get_data(
    dataNames="Position.z"
)

print(position_data.head())
```

```text
  |    |   SessionKey | timestamp    | Utc                          |   DriverNo | Status   |   X |   Y |   Z |
  |---:|-------------:|:-------------|:-----------------------------|-----------:|:---------|----:|----:|----:|
  |  0 |         9574 | 00:01:45.570 | 2024-07-28T12:10:22.7877313Z |          1 | OnTrack  |   0 |   0 |   0 |
  |  1 |         9574 | 00:01:45.570 | 2024-07-28T12:10:22.7877313Z |          2 | OnTrack  |   0 |   0 |   0 |
  |  2 |         9574 | 00:01:45.570 | 2024-07-28T12:10:22.7877313Z |          3 | OnTrack  |   0 |   0 |   0 |
  |  3 |         9574 | 00:01:45.570 | 2024-07-28T12:10:22.7877313Z |          4 | OnTrack  |   0 |   0 |   0 |
  |  4 |         9574 | 00:01:45.570 | 2024-07-28T12:10:22.7877313Z |         10 | OnTrack  |   0 |   0 |   0 |
```

#### Data Processing

LiveF1 uses a medallion architecture to process F1 data into analysis-ready formats:

```python
# Generate processed data tables
session.generate(silver=True)

# Access refined data
laps_data = session.get_laps()
telemetry_data = session.get_car_telemetry()

print(laps_data.head())
```

```text
    |    |   lap_number | lap_time               | in_pit                 | pit_out   | sector1_time           | sector2_time           | sector3_time           | None   |   speed_I1 |   speed_I2 |   speed_FL |   speed_ST |   no_pits | lap_start_time         |   DriverNo | lap_start_date             |
    |---:|-------------:|:-----------------------|:-----------------------|:----------|:-----------------------|:-----------------------|:-----------------------|:-------|-----------:|-----------:|-----------:|-----------:|----------:|:-----------------------|-----------:|:---------------------------|
    |  0 |            1 | NaT                    | 0 days 00:17:07.661000 | NaT       | NaT                    | 0 days 00:00:48.663000 | 0 days 00:00:29.571000 |        |        314 |        204 |            |        303 |         0 | NaT                    |         16 | 2024-07-28 13:03:52.742000 |
    |  1 |            2 | 0 days 00:01:50.240000 | NaT                    | NaT       | 0 days 00:00:31.831000 | 0 days 00:00:48.675000 | 0 days 00:00:29.734000 |        |        303 |        203 |        219 |            |         0 | 0 days 00:57:07.067000 |         16 | 2024-07-28 13:05:45.045000 |
    |  2 |            3 | 0 days 00:01:50.519000 | NaT                    | NaT       | 0 days 00:00:31.833000 | 0 days 00:00:49.132000 | 0 days 00:00:29.554000 |        |        311 |        202 |        215 |        304 |         0 | 0 days 00:58:57.307000 |         16 | 2024-07-28 13:07:35.285000 |
    |  3 |            4 | 0 days 00:01:49.796000 | NaT                    | NaT       | 0 days 00:00:31.592000 | 0 days 00:00:48.778000 | 0 days 00:00:29.426000 |        |        312 |        201 |        217 |        309 |         0 | 0 days 01:00:47.870000 |         16 | 2024-07-28 13:09:25.848000 |
    |  4 |            5 | 0 days 00:01:49.494000 | NaT                    | NaT       | 0 days 00:00:31.394000 | 0 days 00:00:48.729000 | 0 days 00:00:29.371000 |        |        313 |        197 |        217 |        311 |         0 | 0 days 01:02:37.721000 |         16 | 2024-07-28 13:11:15.699000 |
```

### Real-Time Data

Stream live race data:

```python
from livef1.adapters import RealF1Client

# Initialize client with topics to subscribe
client = RealF1Client(
    topics=["CarData.z", "Position.z"],
    log_file_name="race_data.json"  # Optional: log data to file
)

# Define callback for incoming data
@client.callback("telemetry_handler")
async def handle_data(records):
    for record in records:
        print(record)  # Process incoming data

# Start receiving data
client.run()
```

## Documentation

For detailed documentation, examples, and API reference, visit our [documentation page](https://livef1.readthedocs.io/).

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- Report bugs and request features in [GitHub Issues](https://github.com/GoktugOcal/LiveF1/issues)
- For questions and discussions, use [GitHub Discussions](https://github.com/GoktugOcal/LiveF1/discussions)

## FEEL FREE TO [CONTACT ME](https://www.goktugocal.com/contact.html)