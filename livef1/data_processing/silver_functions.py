import pandas as pd
import numpy as np
from datetime import timedelta

def generate_laps_table(bronze_lake):
    df_exp = bronze_lake.get("TimingData")

    sector_cols = {
        "Sectors_0_Value": "sector1_time",
        "Sectors_1_Value": "sector2_time",
        "Sectors_2_Value": "sector3_time",
        "Sectors_0_PreviousValue": None,
        "Sectors_1_PreviousValue": None,
        "Sectors_2_PreviousValue": None
    }

    speedTrap_cols = {
        "Speeds_I1_Value": "speed_I1",
        "Speeds_I2_Value": "speed_I2",
        "Speeds_FL_Value": "speed_FL",
        "Speeds_ST_Value": "speed_ST",
    }
    pit_cols = {
        "InPit": "in_pit",
        "PitOut": "pit_out"
    }

    base_cols = {
        "NumberOfLaps": "lap_number",
        "LastLapTime_Value": "lap_time"
    }

    extra_cols = ["no_pits"]
    extra_raw_cols = ["Stopped"]

    col_map = {**base_cols, **pit_cols, **sector_cols, **speedTrap_cols}
    cols = list(base_cols.values()) + list(pit_cols.values()) + list(sector_cols.values()) + list(speedTrap_cols.values())
    raw_cols = list(base_cols.keys()) + list(pit_cols.keys()) + list(sector_cols.keys()) + list(speedTrap_cols.keys()) + extra_raw_cols

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

    all_laps = []

    for driver_no in df_exp["DriverNo"].unique():
        df_driver = df_exp[df_exp["DriverNo"] == driver_no]
        df_test = df_driver[["timestamp"] + raw_cols].dropna(subset=raw_cols, how="all").replace('', np.nan)

        for col in ["Sectors_0_Value", "Sectors_1_Value", "Sectors_2_Value", "Sectors_0_PreviousValue", "Sectors_1_PreviousValue", "Sectors_2_PreviousValue", "LastLapTime_Value"]:
            df_test[col] = df_test[col]
            df_test[col] = pd.to_timedelta(df_test[col].apply(str_timedelta))

        def enter_new_lap(laps, record):
            if laps is None and record is None:
                no_pits = 0
                laps = []
                record = {key: None if key != "lap_number" else 1 for key in cols}
                record["no_pits"] = no_pits
                return [], record, timedelta(seconds=0)

            if (record["lap_time"] is None) & ((record["sector1_time"] != None) and (record["sector2_time"] != None) and (record["sector3_time"] != None)):
                record["lap_time"] = record["sector1_time"] + record["sector2_time"] + record["sector3_time"]

            laps.append(record)

            no_pits = record["no_pits"]
            record = {key: None if key != "lap_number" else val + 1 for key, val in record.items()}
            record["no_pits"] = no_pits

            return laps, record

        new_lap_allowed = True
        laps, record, last_record_ts = enter_new_lap(None, None)

        for idx, row in df_test.iterrows():
            ts = pd.to_timedelta(row.timestamp)

            if row.Stopped == True:
                laps, record = enter_new_lap(laps, record)
                continue

            if not pd.isnull(row.LastLapTime_Value):
                if not pd.isnull(row.Sectors_2_Value):
                    record[col_map["LastLapTime_Value"]] = row.LastLapTime_Value
                elif not pd.isnull(row.Sectors_2_PreviousValue):
                    laps[-1][col_map["LastLapTime_Value"]] = row.LastLapTime_Value

            for sc_key, sc_value in row[list(speedTrap_cols.keys())].dropna().to_dict().items():
                record[col_map[sc_key]] = sc_value

            for sc_key, sc_value in row[list(pit_cols.keys())].dropna().to_dict().items():
                if sc_key == "InPit":
                    if sc_value == 1:
                        record[col_map[sc_key]] = ts
                elif sc_key == "PitOut":
                    if sc_value == True:
                        record[col_map[sc_key]] = ts
                        record["no_pits"] += 1

            for sc_key, sc_value in row[list(sector_cols.keys())].dropna().to_dict().items():
                sc_no = int(sc_key.split("_")[1])
                key_type = sc_key.split("_")[2]

                if key_type == "Value":
                    if record[f"sector{str(sc_no + 1)}_time"] == None:
                        record[f"sector{str(sc_no + 1)}_time"] = sc_value
                        last_record_ts = ts
                        if sc_no == 2:
                            laps, record = enter_new_lap(laps, record)
                            record["lap_start_time"] = ts
                    elif sc_value == record[str(sc_no + 1)]:
                        pass
                    elif ts - last_record_ts > timedelta(seconds=10):
                        laps, record = enter_new_lap(laps, record)
                        record[f"sector{str(sc_no + 1)}_time"] = sc_value
                        last_record_ts = ts

                elif key_type == "PreviousValue" and ts - last_record_ts > timedelta(seconds=10):
                    record[f"sector{str(sc_no + 1)}_time"] = sc_value
                    last_record_ts = ts
                    if sc_no == 2:
                        laps, record = enter_new_lap(laps, record)

        laps_df = pd.DataFrame(laps)
        laps_df["DriverNo"] = driver_no
        all_laps.append(laps_df)

    all_laps_df = pd.concat(all_laps, ignore_index=True)

    segments = ["sector1_time", "sector2_time", "sector3_time"]
    for idx in range(len(segments)):
        rest = np.delete(segments, idx)
        all_laps_df[segments[idx]] = (all_laps_df[segments[idx]].fillna(timedelta(minutes=0)) + (all_laps_df[segments[idx]].isnull() & (all_laps_df["lap_number"] > 1)) * (all_laps_df[segments[idx]].isnull() * (all_laps_df["lap_time"].fillna(timedelta(minutes=0)) - all_laps_df[rest].sum(axis=1)))).replace(timedelta(minutes=0), np.timedelta64("NaT"))

    new_ts = (all_laps_df["lap_start_time"] + all_laps_df["lap_time"]).shift(1)
    all_laps_df["lap_start_time"] = (new_ts.isnull() * all_laps_df["lap_start_time"]) + new_ts.fillna(timedelta(0))

    all_laps_df[["lap_start_time"] + all_laps_df.columns.tolist()]
    return all_laps_df
