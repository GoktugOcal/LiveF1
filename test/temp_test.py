from livef1.adapters.realtime_client import RealF1Client
import datetime
import json

import livef1

# Initialize client
client = RealF1Client(
    topics=["DriverList"],
    log_file_name="session_data.json"
)

# Define multiple handlers
@client.callback("process_telemetry")
async def handle_telemetry(records):
    # Process car telemetry data
    telemetry_data = records.get("DriverList")
    if telemetry_data:
        for record in telemetry_data:
            print("Driver >", record) # this is a placeholder for your code

# @client.callback("track_status")
# async def handle_track_status(records):
#     # Monitor track conditions
#     track_data = records.get("TrackStatus")
#     if track_data:
#         for record in track_data:
#             print("Track -", record) # this is a placeholder for your code


# Start the client
client.run()