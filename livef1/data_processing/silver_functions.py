import pandas as pd
import numpy as np
from datetime import timedelta
import re

from ..utils.helper import to_datetime
from ..utils.constants import (
    interpolation_map, 
    silver_cartel_col_order, 
    silver_laps_col_order, 
    FIA_CATEGORY_SCOPE_RULES, 
    penalty_types
)

def add_distance_to_lap(lap_df, start_x, start_y, x_coeff, y_coeff):
    """
    Calculates the cumulative distance covered by a car during a lap based on its speed and timestamp.
    Adjusts the distance based on the starting line coordinates and direction.

    Args:
        lap_df (pd.DataFrame): DataFrame containing lap data with columns 'speed', 'timestamp', 'X', and 'Y'.
        start_x (float): X-coordinate of the starting line.
        start_y (float): Y-coordinate of the starting line.
        x_coeff (float): Coefficient for determining direction along the X-axis.
        y_coeff (float): Coefficient for determining direction along the Y-axis.

    Returns:
        pd.DataFrame: Updated DataFrame with a new 'Distance' column representing the cumulative distance.
    """

    if len(lap_df) > 0:
        # Calculate cumulative distance based on speed and time difference
        dt_diff = lap_df["timestamp"].diff().dt.total_seconds()
        # dt_diff.iloc[0] = lap_df["timestamp"].iloc[0].total_seconds()
        dt_diff.iloc[0] = 0
        lap_df["Distance"] = ((((lap_df.Speed + lap_df.Speed.shift(1)) / 2) / 3.6) * dt_diff).cumsum()

        # Get the first row to determine the starting line position
        start_line = lap_df.iloc[0]

        # Determine the direction based on the starting line coordinates and coefficients
        if ((start_line.X - start_x) / x_coeff > 0) & ((start_line.Y - start_y) / y_coeff > 0):
            direction = 1
        else:
            direction = -1

        # Calculate the initial distance from the starting line
        distance = direction * (((start_line.X - start_x)**2 + (start_line.Y - start_y)**2)**0.5) / 10

        # Adjust the cumulative distance with the initial distance
        # lap_df["Distance"] = distance + lap_df["Distance"].fillna(0)
        lap_df["Distance"] = distance + lap_df["Distance"]

    return lap_df

def add_track_status(laps_df, df_track):
    temp_df = laps_df.copy()
    temp_df = temp_df.set_index("LapStartTime").join(df_track.set_index("timestamp")[["Status","Message"]], how="outer")
    temp_df.LapNo = temp_df.LapNo.ffill()

    temp_df.Status = temp_df.Status.ffill().bfill()
    laps_df = laps_df.set_index("LapNo").join(temp_df.groupby("LapNo").Status.unique().apply(lambda x: ",".join(x))).reset_index().rename(columns={"Status":"TrackStatus"})
    # temp_df.Message = temp_df.Message.ffill()
    # laps_df = laps_df.set_index("LapNo").join(temp_df.groupby("LapNo").Message.unique().apply(lambda x: ",".join(x))).reset_index()

    return laps_df

def add_track_status_telemetry(telemetry_df, df_track):

    telemetry_df = telemetry_df.set_index("timestamp").join(df_track.set_index("timestamp")[["Status"]]).rename(columns={"Status":"TrackStatus"})
    telemetry_df.TrackStatus = telemetry_df.TrackStatus.ffill()
    return telemetry_df.dropna(subset="SessionKey").reset_index()

def add_lineposition(telemetry_df, df_tmg):
    telemetry_df = telemetry_df.set_index("timestamp").join(df_tmg.set_index("timestamp")[["Position"]], how="outer")
    telemetry_df.Position = telemetry_df.Position.ffill()
    return telemetry_df.reset_index()

def generate_laps_table(session, df_exp, df_rcm, df_tyre, df_track):

    def delete_laps(laps_df, df_rcm):
        laps_df["IsDeleted"] = False

        df_rcm_del = df_rcm[(df_rcm["Category"] == "Other") & (df_rcm.Message.str.split(" ").str[0] == "CAR")]
        df_rcm_del["deleted_driver"] = df_rcm_del.Message.str.split(" ").str[1]
        df_rcm_del["deleted_type"] = df_rcm_del.Message.str.split(" ").str[3]
        df_rcm_del["deleted_time"] = df_rcm_del.apply(lambda x: x.Message.split(" ")[4] if x.deleted_type == "TIME" else None, axis=1)

        for idx, row in df_rcm_del[df_rcm_del["Message"].str.contains("REINSTATED") & (df_rcm_del["deleted_type"] == "TIME")].iterrows():
            driver = row.deleted_driver
            time = row.deleted_time
            df_rcm_del = df_rcm_del.drop(df_rcm_del[(df_rcm_del.deleted_driver == driver) & (df_rcm_del.deleted_time == time)].index)

        def lap_finder(x):
            if len(x.Message.split(" ")) > 12:
                if x.deleted_type == "LAP":
                    return x.Message.split(" ")[12]
                elif x.deleted_type == "TIME":
                    return x.Message.split(" ")[13]
                else:
                    return None
            else:
                return None

        if len(df_rcm_del) > 0:
            df_rcm_del["deleted_lap"] = df_rcm_del.apply(lambda x: lap_finder(x), axis=1)

            for idx, row in df_rcm_del.iterrows():
                try: int(row["deleted_lap"])
                except: continue
                row_bool = (laps_df["LapNo"] == int(row["deleted_lap"])) & (laps_df["DriverNo"] == row["deleted_driver"])
                laps_df.loc[row_bool, "IsDeleted"] = True
                laps_df.loc[row_bool, "DeletionMessage"] = row["Message"]
            
        
        return laps_df

    df_tyre["timestamp"] = pd.to_timedelta(df_tyre["timestamp"])
    sessionKey = df_exp["SessionKey"].values[0]

    if "_deleted" not in df_exp.columns:
        df_exp["_deleted"] = None
    else:
        df_exp["_deleted"] = df_exp["_deleted"].fillna(False)

    sector_cols = {
        "Sectors_0_Value": "Sector1_Time",
        "Sectors_1_Value": "Sector2_Time",
        "Sectors_2_Value": "Sector3_Time",
        "Sectors_0_PreviousValue": None,
        "Sectors_1_PreviousValue": None,
        "Sectors_2_PreviousValue": None
    }

    speedTrap_cols = {
        "Speeds_I1_Value": "Speed_I1",
        "Speeds_I2_Value": "Speed_I2",
        "Speeds_FL_Value": "Speed_FL",
        "Speeds_ST_Value": "Speed_ST",
    }
    pit_cols = {
        "InPit": "PitIn",
        "PitOut": "PitOut"
    }

    base_cols = {
        "NumberOfLaps": "LapNo",
        "LastLapTime_Value": "LapTime"
    }

    misc_cols = {
        "Position": "Position"
    }
    if session.type == "Race":
        misc_cols["GapToLeader"] = "GapToLeader"
        misc_cols["IntervalToPositionAhead_Value"] = "IntervalToPositionAhead"

    extra_cols = [
        "NoPits",
        "sector1_finish_timestamp",
        "sector2_finish_timestamp",
        "sector3_finish_timestamp"
        ]
    extra_raw_cols = ["RacingNumber","Stopped","_deleted"]

    col_map = {**base_cols, **pit_cols, **sector_cols, **speedTrap_cols, **misc_cols}
    cols = list(base_cols.values()) + list(pit_cols.values()) + list(sector_cols.values()) + list(speedTrap_cols.values()) + list(misc_cols.values())
    raw_cols = list(base_cols.keys()) + list(pit_cols.keys()) + list(sector_cols.keys()) + list(speedTrap_cols.keys()) + list(misc_cols.keys()) + extra_raw_cols

    def str_timedelta(x):
        if isinstance(x, str):
            count_sep = x.count(":")
            if count_sep == 0:
                return "00:00:" + x
            elif count_sep == 1:
                return "00:" + x
            else:
                return x
        else:
            return x
    
    def enter_new_lap(laps, record):
        if laps is None and record is None:
            NoPits = 0
            laps = []
            record = {key: None if key != "LapNo" else 1 for key in cols}
            record["NoPits"] = NoPits
            return [], record, timedelta(seconds=0)

        if (record["LapTime"] is None) & ((record["Sector1_Time"] != None) and (record["Sector2_Time"] != None) and (record["Sector3_Time"] != None)):
            record["LapTime"] = record["Sector1_Time"] + record["Sector2_Time"] + record["Sector3_Time"]

        last_position = record["Position"]
        laps.append(record)
        NoPits = record["NoPits"]
        record = {key: None if key != "LapNo" else val + 1 for key, val in record.items()}
        record["NoPits"] = NoPits
        record["Position"] = last_position

        return laps, record

    all_laps = []

    for driver_no in df_exp["DriverNo"].unique():
        df_driver = df_exp[df_exp["DriverNo"] == driver_no]
        df_test = df_driver[["timestamp"] + raw_cols].dropna(subset=raw_cols, how="all").replace('', np.nan)

        for col in ["Sectors_0_Value", "Sectors_1_Value", "Sectors_2_Value", "Sectors_0_PreviousValue", "Sectors_1_PreviousValue", "Sectors_2_PreviousValue", "LastLapTime_Value"]:
            df_test[col] = df_test[col]
            df_test[col] = pd.to_timedelta(df_test[col].apply(str_timedelta))

        new_lap_allowed = True
        laps, record, last_record_ts = enter_new_lap(None, None)

        for idx, row in df_test[df_test.RacingNumber.isna()].iterrows():
            ts = pd.to_timedelta(row.timestamp)

            if row.Stopped == True:
                laps, record = enter_new_lap(laps, record)
                continue

            if not pd.isnull(row.LastLapTime_Value):
                if not pd.isnull(row.Sectors_2_Value):
                    record[col_map["LastLapTime_Value"]] = row.LastLapTime_Value
                elif not pd.isnull(row.Sectors_2_PreviousValue):
                    laps[-1][col_map["LastLapTime_Value"]] = row.LastLapTime_Value

            ## Iterate over all columns
            for sc_key, sc_value in row.to_dict().items():
                if (sc_key == "_deleted"): continue
                
                elif not pd.isna(sc_value):
                    
                    if sc_key in speedTrap_cols:
                        record[col_map[sc_key]] = float(sc_value)
                    
                    elif sc_key in pit_cols:
                        if sc_key == "InPit":
                            if sc_value == 1:
                                record[col_map[sc_key]] = ts
                        elif sc_key == "PitOut":
                            if sc_value == True:
                                record[col_map[sc_key]] = ts
                                record["NoPits"] += 1
                    

                    elif sc_key in misc_cols:
                        if sc_key == "Position":
                            if sc_value is not None:
                                record[col_map[sc_key]] = sc_value
                        elif sc_key == "GapToLeader":
                            if sc_value is not None:
                                if "LAP" in sc_value:
                                    record[col_map[sc_key]] = float(0)
                                elif "L" in sc_value:
                                    record[col_map[sc_key]] = None
                                elif sc_value == "":
                                    record[col_map[sc_key]] = None
                                else:
                                    record[col_map[sc_key]] = float(sc_value)
                        elif sc_key == "IntervalToPositionAhead_Value":
                            if sc_value is not None:
                                if "LAP" in sc_value:
                                    record[col_map[sc_key]] = float(0)
                                elif "L" in sc_value:
                                    record[col_map[sc_key]] = None
                                elif sc_value == "":
                                    record[col_map[sc_key]] = None
                                else:
                                    record[col_map[sc_key]] = float(sc_value)

                    elif sc_key in sector_cols:
                        sc_no = int(sc_key.split("_")[1])
                        key_type = sc_key.split("_")[2]

                        if key_type == "Value":
                            if record[f"Sector{str(sc_no + 1)}_Time"] == None:
                                record[f"Sector{str(sc_no + 1)}_Time"] = sc_value
                                last_record_ts = ts
                                if sc_no == 2:
                                    laps, record = enter_new_lap(laps, record)
                                    record["LapStartTime"] = ts
                            elif sc_value == record[f"Sector{str(sc_no + 1)}_Time"]:
                                pass
                            elif ts - last_record_ts > timedelta(seconds=10):
                                laps, record = enter_new_lap(laps, record)
                                record[f"Sector{str(sc_no + 1)}_Time"] = sc_value
                                record["LapStartTime"] = ts - sc_value
                                last_record_ts = ts
                        
                        elif key_type == "PreviousValue":
                            if sc_no != 2:
                                record[f"Sector{str(sc_no + 1)}_Time"] = sc_value
                                last_record_ts = ts
                            elif len(laps) > 0:
                                laps[-1][f"Sector{str(sc_no + 1)}_Time"] = sc_value
                                last_record_ts = ts

        # Aggregate all laps data of the driver
        laps_df = pd.DataFrame(laps)    
        laps_df["DriverNo"] = driver_no
        if "LapStartTime" in laps_df.columns: laps_df = add_track_status(laps_df, df_track)
        all_laps.append(laps_df)

    all_laps_df = pd.concat(all_laps, ignore_index=True)
    
    new_ts = (all_laps_df["LapStartTime"] + all_laps_df["LapTime"]).shift(1)
    all_laps_df["LapStartTime"] = (new_ts.isnull() * all_laps_df["LapStartTime"]) + new_ts.fillna(timedelta(0))
    all_laps_df["LapStartDate"] = (all_laps_df["LapStartTime"] + session.first_datetime).fillna(session.session_start_datetime)
    all_laps_df["LapStartTime"] = all_laps_df["LapStartTime"].fillna(all_laps_df.iloc[1].LapStartTime - (all_laps_df.iloc[1].LapStartDate - all_laps_df.iloc[0].LapStartDate))

    # Delete laps
    all_laps_df = delete_laps(all_laps_df, df_rcm)

    # Add session data
    all_laps_df["SessionKey"] = sessionKey
    # Add driver data
    all_laps_df["Driver"] = all_laps_df["DriverNo"].map(session.drivers)

    # Add pit data
    # if session.check_data_name("PitStopSeries"):
    if "PitStopSeries" in session.topic_names_info:
        # Get Pit Stop Data
        df_pit = session.get_data("PitStopSeries", level="bronze")
        df_pit = df_pit[["RacingNumber", "PitStopTime", "PitLaneTime", "Lap"]].rename(columns={"RacingNumber": "DriverNo", "Lap":"LapNo", "PitStopTime": "PitStopDuration", "PitLaneTime":"PitLaneDuration"})
        df_pit["LapNo"] = df_pit["LapNo"].astype(int)
        all_laps_df = all_laps_df.set_index(["DriverNo", "LapNo"]).join(df_pit.set_index(["DriverNo", "LapNo"])).reset_index()
    
    # Add tyre data
    all_laps_df["LapEndTime"] = all_laps_df["LapStartTime"] + all_laps_df["LapTime"]
    all_laps_df = all_laps_df.set_index(["DriverNo", "LapEndTime"]).join(
        df_tyre.rename(columns={"timestamp":"LapEndTime", "TotalLaps":"TyreAge"}).set_index(["DriverNo", "LapEndTime"]),
        how="outer"
    )
    all_laps_df[["Compound","New","TyreAge"]] = all_laps_df.groupby('DriverNo')[["Compound","New","TyreAge"]].ffill()
    all_laps_df = all_laps_df.reset_index().dropna(subset = "SessionKey")

    for col in silver_laps_col_order:
        if col not in all_laps_df.columns:
            all_laps_df[col] = None

    return all_laps_df[silver_laps_col_order]

def assign_regions(tel_cor, df_corners):

    # Example: same bins_df as above
    conditions = [
        (tel_cor["Distance"] >= row['corner_start']) & (tel_cor["Distance"] < row['corner_end']) if row["corner_end"] >= row["corner_start"]
        else (tel_cor["Distance"] >= row['corner_start']) | (tel_cor["Distance"] < row['corner_end'])
        for _, row in df_corners.iterrows()
    ]
    choices = df_corners['name'].tolist()

    return np.select(conditions, choices, default=None)

def generate_car_telemetry_table(session, df_car, df_pos, df_tyre, laps, df_track, df_tmg, df_circuits):
    """
    Generates a telemetry table for car data by combining and processing position and car data
    from the provided BronzeLake object. The function interpolates missing data, aligns it with
    session laps, and calculates cumulative distance covered during each lap.
    Args:
        bronze_lake (BronzeLake): An object containing the raw position and car data, as well as
                                  session and circuit information.
    Returns:
        pd.DataFrame: A DataFrame containing processed telemetry data for all drivers, including:
                      - DriverNo: Driver number.
                      - Utc: Timestamp in UTC.
                      - LapNo: Lap number for the driver.
                      - Distance: Cumulative distance covered during the lap.
                      - SessionKey: Session identifier.
                      - timestamp: Time elapsed since the session start.
                      - Other interpolated and processed telemetry data.
    Notes:
        - The function interpolates missing data based on predefined interpolation methods.
        - Data is filtered to include only timestamps within the lap start and end times.
        - Cumulative distance is calculated for each lap using speed and timestamp data, adjusted
          for the circuit's starting line position and direction.
    Raises:
        ValueError: If required data is missing or cannot be processed.
    """
    # Get position data
    df_pos["Utc"] = to_datetime(df_pos["Utc"])
    df_pos["tag"] = "position"

    # Get car data
    df_car["Utc"] = to_datetime(df_car["Utc"])
    df_car["timestamp"] = pd.to_timedelta(df_car["timestamp"])
    df_car["tag"] = "car"

    # Get tyre data
    df_tyre["timestamp"] = pd.to_timedelta(df_tyre["timestamp"])

    # Join car and position data
    df = df_car \
        .set_index(["DriverNo", "Utc"]) \
        .join(df_pos.set_index(["DriverNo", "Utc"]), rsuffix="_pos", how="outer") \
        .reset_index().sort_values(["DriverNo", "Utc"]) \
        .rename(columns={"Status":"CarStatus"})
    df["CarStatus"] = df["CarStatus"].ffill()

    df["tag"] = df["tag"].fillna("") + df["tag_pos"].fillna("")

    all_drivers_data = []

    for driver_no in df["DriverNo"].unique():
        
        df_driver = df[df["DriverNo"] == driver_no].set_index("Utc")

        laps = session.data_lake.silver.lake["laps"].df
        laps_driver = laps[laps["DriverNo"] == driver_no]

        for col in df_driver.columns:
            if col in interpolation_map:
                if len(df_driver[col].dropna()) < len(df_driver)*0.2:
                    continue
                df_driver[col] = df_driver[col].interpolate(method=interpolation_map[col], order=2).values

        laps_driver.loc[:, "lap_end_date"] = laps_driver["LapStartDate"] + laps_driver["LapTime"]

        df_driver = df_driver.join(laps_driver[["LapStartDate", "LapNo"]].set_index("LapStartDate"), how="outer")

        df_driver["LapNo"] = df_driver["LapNo"].ffill().bfill()
        df_driver.index.names = ['Utc']

        df_driver = df_driver.reset_index()
        df_driver = df_driver[df_driver.Utc.between(laps_driver["LapStartDate"].min(), laps_driver["lap_end_date"].max())]

        df_driver["SessionKey"] = df_driver["SessionKey"].ffill().bfill()
        df_driver["timestamp"] = df_driver["Utc"] - session.first_datetime

        df_driver = df_driver.dropna(subset=["DriverNo"])

        # Iterate through each unique lap number for the driver to calculate and add the cumulative distance
        # covered during the lap based on speed and timestamp, adjusted for the starting line position.
        for lap_no in df_driver["LapNo"].unique():
            lap_df = df_driver[df_driver["LapNo"] == lap_no]
            if hasattr(session.meeting.circuit, "start_coordinates"):
                lap_df = add_distance_to_lap(
                    lap_df,
                    session.meeting.circuit.start_coordinates[0],
                    session.meeting.circuit.start_coordinates[1],
                    session.meeting.circuit.start_direction[0],
                    session.meeting.circuit.start_direction[1]
                    )
                            
                df_driver.loc[lap_df.index, "Distance"] = lap_df["Distance"].values
            else:
                df_driver.loc[lap_df.index, "Distance"] = None
        
        df_driver = add_track_status_telemetry(df_driver, df_track)
        df_driver = add_lineposition(df_driver, df_tmg[df_tmg.DriverNo == driver_no])

        ## TODO: Add race distance
        # if len(df_driver) > 0:
        #     race_distance = add_distance_to_lap(
        #         df_driver.copy(),
        #         session.meeting.circuit.start_coordinates[0],
        #         session.meeting.circuit.start_coordinates[1],
        #         session.meeting.circuit.start_direction[0],
        #         session.meeting.circuit.start_direction[1]
        #     )["Distance"].values
        #     df_driver["RaceDistance"] = race_distance
        #     print("added race distance :", driver_no, race_distance)

        all_drivers_data.append(df_driver)

    all_drivers_df = pd.concat(all_drivers_data, ignore_index=True)

    # Add Tyre Data
    all_drivers_df = all_drivers_df.set_index(["DriverNo", "timestamp"]).join(
        df_tyre.rename(columns={"TotalLaps":"TyreAge"}).set_index(["DriverNo", "timestamp"]),
        how="outer"
    )
    all_drivers_df[["Compound","New","TyreAge"]] = all_drivers_df.groupby('DriverNo')[["Compound","New","TyreAge"]].ffill()
    all_drivers_df = all_drivers_df.reset_index().dropna(subset = ["SessionKey"])

    if hasattr(session.meeting.circuit, "start_coordinates"):
        all_drivers_df["TrackRegion"] = assign_regions(all_drivers_df, df_circuits)
    else:
        all_drivers_df["TrackRegion"] = None

    return all_drivers_df[silver_cartel_col_order]

def generate_race_control_messages_table(session, rcm_df):
    """
    Processes and generates a DataFrame of race control messages for a given session.

    This function takes race control messages and session context, parses category and scope information,
    and structures the data for analysis. It does not interpolate values or align events to lap distances,
    but instead extracts and organizes categorical details (such as category, scope, flag, mode, and status)
    found in race control messages.

    Args:
        session: The session object containing circuit and meeting information.
        df_rcm (pd.DataFrame): DataFrame containing raw race control messages with at least the columns
            ['Message', 'Category', 'Scope', 'Flag', 'Mode', 'Status'].

    Returns:
        pd.DataFrame: A DataFrame with processed race control message records, including extracted and clarified
            category and scope values for each message, along with relevant timestamps and context fields.
    """

    def parse_cars_from_message(message):
        """
        Parse car numbers from race control messages.
        Handles two distinct cases:
        1. Messages with "CAR" (singular) - extracts single car numbers
        2. Messages with "CARS" (plural) - extracts multiple car numbers
        
        Avoids extracting:
        - Lap numbers (LAP 8, LAP 14)
        - Timestamps (15:11:52, 16:05.442)
        - Turn numbers (TURN 11, TURN 5)
        - Lap times (1:12.542)
        """
        if pd.isna(message) or not message:
            return None
        
        cars = []
        message_upper = message.upper()
        
        # Helper function to check if a number is likely a car number (not lap, turn, timestamp, etc.)
        def is_valid_car_number(num_str, context_before, context_after):
            """Check if a number is a valid car number based on surrounding context."""
            # Check if it's part of a timestamp pattern (HH:MM:SS or MM:SS)
            if re.search(r'\d+\s*:\s*' + re.escape(num_str) + r'\s*:\s*\d+', context_before + num_str + context_after):
                return False
            if re.search(re.escape(num_str) + r'\s*:\s*\d+', context_after):
                return False
            
            # Check if it's a lap number (LAP followed by number)
            if re.search(r'LAP\s+' + re.escape(num_str) + r'\b', context_before + num_str + context_after, re.IGNORECASE):
                return False
            
            # Check if it's a turn number (TURN followed by number)
            if re.search(r'TURN\s+' + re.escape(num_str) + r'\b', context_before + num_str + context_after, re.IGNORECASE):
                return False
            
            # Check if it's part of a lap time (like 1:12.542 or 16:05.442)
            # Pattern: digit(s):digit(s).digit(s) or digit(s):digit(s):digit(s)
            if re.search(r'\d+\s*:\s*' + re.escape(num_str) + r'\s*\.\s*\d+', context_before + num_str + context_after):
                return False
            
            return True
        
        # Case 1: Handle "CAR" (singular) patterns
        # Check if message contains "CAR " but not "CARS " (to avoid matching "CARS" as "CAR")
        if re.search(r'\bCAR\s+', message_upper) and not re.search(r'\bCARS\s+', message_upper):
            # Pattern: "CAR" followed by number, optionally followed by "(DRIVER_CODE)"
            # Examples: "CAR 23 (ALB)", "CAR 55 (SAI) TIME", "INCIDENT INVOLVING CAR 55"
            car_pattern = r'(?i)\bCAR\s+(\d+)'
            matches = list(re.finditer(car_pattern, message))
            
            for match in matches:
                car_num = match.group(1)
                match_start = match.start()
                match_end = match.end()
                
                # Get context around the match
                context_before = message[max(0, match_start - 30):match_start]
                context_after = message[match_end:min(len(message), match_end + 30)]
                
                # Check if this is a valid car number (not lap, turn, timestamp, etc.)
                if is_valid_car_number(car_num, context_before, context_after):
                    cars.append(int(car_num))
        
        # Case 2: Handle "CARS" (plural) patterns
        elif re.search(r'\bCARS\s+', message_upper):
            # Pattern: "CARS" followed by numbers with driver codes in parentheses
            # Handles: "CARS 44 (HAM) AND 18 (STR)", "CARS 63 (RUS), 18 (STR), 2 (SAR)", etc.
            # Match from "CARS" to the end of the car list (stops at keywords like "NOTED", "WILL", etc.)
            # The pattern matches: number + (driver_code) + (comma or AND) + (repeat)
            cars_pattern = r'(?i)\bCARS\s+((?:\d+\s*\([^)]+\)(?:\s*,\s*|\s+AND\s+)?)+?)(?=\s+(?:NOTED|WILL|REVIEWED|NO|FIA|$))'
            cars_match = re.search(cars_pattern, message)
            
            if cars_match:
                # Extract the section with car numbers
                cars_section = cars_match.group(1)
                # Extract all numbers that are followed by parentheses (driver codes)
                # This ensures we only get car numbers, not other numbers in the message
                car_numbers = re.findall(r'(\d+)\s*\([^)]+\)', cars_section)
                
                for num in car_numbers:
                    cars.append(int(num))
            else:
                # Fallback: if the lookahead pattern doesn't match, try without it
                cars_pattern_fallback = r'(?i)\bCARS\s+((?:\d+\s*\([^)]+\)(?:\s*,\s*|\s+AND\s+)?)+)'
                cars_match = re.search(cars_pattern_fallback, message)
                if cars_match:
                    cars_section = cars_match.group(1)
                    # Limit to reasonable length to avoid matching too much
                    if len(cars_section) < 200:  # Reasonable limit for car list
                        car_numbers = re.findall(r'(\d+)\s*\([^)]+\)', cars_section)
                        for num in car_numbers:
                            cars.append(int(num))
        
        # Remove duplicates while preserving order
        seen = set()
        unique_cars = []
        for car in cars:
            if car not in seen:
                seen.add(car)
                unique_cars.append(car)
        
        return unique_cars if unique_cars else None

    def parse_category_scope(row):

        message = row.Message.upper()
        category = row.Category
        scope = row.Scope
        flag = row.Flag
        if hasattr(row, "Mode"):
            mode = row.Mode
        else:
            mode = None
        status = row.Status

        if pd.isna(message):
            return "Unknown", "Unknown", None, None

        if category == "Flag":
            if scope == "Driver":
                clean_message = message \
                    .replace(flag,"") \
                    .replace("WAVED","") \
                    .replace("FLAG","") \
                    .replace("FOR","") \
                    .strip()
                
                if flag == "BLUE":
                    info = clean_message.split(" ")[-1]
                elif flag == "BLACK AND WHITE":
                    info = clean_message.split("-")[-1].strip()
            
            elif scope == "Sector":
                clean_message = message
                sector = clean_message.split("SECTOR")[-1].strip()
                info = f"SECTOR {sector}"

            elif scope == "Track":
                clean_message = message
                info = clean_message.split("-")[-1].strip()
            return category, scope, status, info

        elif category == "Drs":
            clean_message = message
            scope = clean_message.split(" ")[-1].strip()
            info = None
            return category, scope, status, info
        
        elif category == "SafetyCar":
            scope = mode
            info = status
            return category, scope, status, info
        
        elif category == "Other":
            info = None
            for category, scopes in FIA_CATEGORY_SCOPE_RULES.items():
                for scope, keywords in scopes.items():
                    if any(k in message for k in keywords):
                        if "-" in message:
                            info = message.split("-")[-1].strip()

                        if category == "Penalty":
                            penalty_type = None
                            for pt in penalty_types:
                                if pt in message:
                                    penalty_type = pt
                                    break
                            
                            if penalty_type == "TIME PENALTY":
                                match = re.search(r'(\d{1,2})(?=\s*SECOND)', message)
                                penalty_value = match.group(1) if match else None
                            else: penalty_value = None
                            
                            if "PENALTY SERVED" in message: status = "Served"
                            else: status = None

                            info = penalty_value
                            
                        return category, scope, status, info

        else:
            return "Other", "Unclassified", None, None

    rcm_df["RacingNumber"] = rcm_df.Message.apply(lambda x: parse_cars_from_message(x))

    rcm_df[["Category", "Scope", "Status", "info"]] = (
        rcm_df
        .apply(lambda m: pd.Series(parse_category_scope(m)), axis=1)
    )

    return rcm_df[
        [
            "SessionKey", 
            "timestamp", 
            "Utc",
            "Category", 
            "Scope",
            "Status", 
            "Flag", 
            "Message", 
            "Lap",
            "RacingNumber",
            "info"
        ]
    ]