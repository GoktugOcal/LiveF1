import livef1
import requests
import pandas as pd
import numpy as np
import json

def get_circuit_data():
    HEADERS = {'User-Agent': 'LiveF1/trial'}

    headers=HEADERS

    response = requests.get("https://api.multiviewer.app/api/v1/circuits", headers=HEADERS)
    if response.status_code == 200:
        circuits_data = response.json()
        return circuits_data
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")

def collect_sessions_by_circuit(circuits_data):
    # sessions = []
    for key, circ in circuits_data.items():
        circ_name = circ["name"]
        circ_years = circ["years"]
        circ_years.append(2023)
        circ_years.append(2025)

        for year in circ_years:
            try:
                session = livef1.get_session(
                    year,
                    meeting_identifier = circ_name,
                    session_identifier = "Race"
                    )
                session.generate()
                # sessions.append(session)
                break
            except:
                pass

    return sessions

def find_starting_coordinates(session):

    car_tel = session.carTelemetry.copy()
    sample = car_tel[car_tel["lap_number"] > 1].dropna(subset=["X", "Y"]).head(2)

    x_chng = sample.X.values[-1] - sample.X.values[0]
    y_chng = sample.Y.values[-1] - sample.Y.values[0]
    x_coeff = x_chng / abs(x_chng)
    y_coeff = y_chng / abs(y_chng)

    laps = session.laps

    filtered_laps = laps[laps["in_pit"].isnull() & laps["pit_out"].isnull() & ~laps["isDeleted"]]
    filter_tuples = list(zip(filtered_laps["DriverNo"], filtered_laps["lap_number"]))
    session.carTelemetry["driver_lap_tuple"] = list(zip(session.carTelemetry["DriverNo"], session.carTelemetry["lap_number"]))
    filtered_df = session.carTelemetry[session.carTelemetry["driver_lap_tuple"].isin(filter_tuples)]

    last_points = filtered_df.groupby(["DriverNo", "lap_number"]).last().reset_index()

    # Calculate IQR for X and Y
    Q1_X = last_points['X'].quantile(0.25)
    Q3_X = last_points['X'].quantile(0.75)
    IQR_X = Q3_X - Q1_X

    Q1_Y = last_points['Y'].quantile(0.25)
    Q3_Y = last_points['Y'].quantile(0.75)
    IQR_Y = Q3_Y - Q1_Y

    # Define bounds for X and Y
    lower_bound_X = Q1_X - 1.5 * IQR_X
    upper_bound_X = Q3_X + 1.5 * IQR_X

    lower_bound_Y = Q1_Y - 1.5 * IQR_Y
    upper_bound_Y = Q3_Y + 1.5 * IQR_Y

    # Filter out outliers
    last_points_filtered = last_points[
        (last_points['X'] >= lower_bound_X) & (last_points['X'] <= upper_bound_X) &
        (last_points['Y'] >= lower_bound_Y) & (last_points['Y'] <= upper_bound_Y)
    ]

    last_points = filtered_df.groupby(["DriverNo", "lap_number"]).last().reset_index()

    limit = 95
    limit_x = 100 - limit if x_coeff < 0 else limit
    limit_y = 100 - limit if y_coeff < 0 else limit

    start_x = np.percentile(last_points_filtered["X"], limit_x)
    start_y = np.percentile(last_points_filtered["Y"], limit_y)

    return start_x, start_y, x_coeff, y_coeff

if __name__ == "__main__":

    circuit_data = get_circuit_data()
    # sessions = collect_sessions_by_circuit(circuit_data)
    
    coordinates = {}
    for key, circ in circuit_data.items():
        circ_name = circ["name"]
        circ_years = circ["years"]
        circ_years.append(2023)
        circ_years.append(2025)

        for year in circ_years:
            try:
                session = livef1.get_session(
                    year,
                    meeting_identifier = circ_name,
                    session_identifier = "Race"
                    )
                session.generate()

                start_x, start_y, x_coeff, y_coeff = find_starting_coordinates(session)

                coordinates[session.meeting.circuit["ShortName"]] = {
                    "start_coordinates": (start_x, start_y),
                    "start_direction": (x_coeff, y_coeff),
                }

                del session

                break
            except:
                pass
    
    with open("starting_coordinates.json", "w") as f:
        json.dump(coordinates, f, indent=4)
    print("Starting coordinates and directions saved to starting_coordinates.json")
