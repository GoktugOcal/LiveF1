import pandas as pd
import numpy as np
from datetime import timedelta

from ..utils.helper import to_datetime
from ..utils.constants import interpolation_map

def generate_laps_table(bronze_lake):
    df_exp = bronze_lake.get("TimingData")
    df_rcm = bronze_lake.get("RaceControlMessages")

    if "_deleted" not in df_exp.columns:
        df_exp["_deleted"] = None
    else:
        df_exp["_deleted"] = df_exp["_deleted"].fillna(False)

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

    extra_cols = [
        "no_pits",
        "sector1_finish_timestamp",
        "sector2_finish_timestamp",
        "sector3_finish_timestamp"
        ]
    extra_raw_cols = ["RacingNumber","Stopped","_deleted"]

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
                        record[col_map[sc_key]] = sc_value
                    
                    elif sc_key in pit_cols:
                        if sc_key == "InPit":
                            if sc_value == 1:
                                record[col_map[sc_key]] = ts
                        elif sc_key == "PitOut":
                            if sc_value == True:
                                record[col_map[sc_key]] = ts
                                record["no_pits"] += 1
                    elif sc_key in sector_cols:
                        sc_no = int(sc_key.split("_")[1])
                        key_type = sc_key.split("_")[2]

                        if key_type == "Value":
                            if record[f"sector{str(sc_no + 1)}_time"] == None:
                                record[f"sector{str(sc_no + 1)}_time"] = sc_value
                                last_record_ts = ts
                                if sc_no == 2:
                                    laps, record = enter_new_lap(laps, record)
                                    record["lap_start_time"] = ts
                            elif sc_value == record[f"sector{str(sc_no + 1)}_time"]:
                                pass
                            elif ts - last_record_ts > timedelta(seconds=10):
                                laps, record = enter_new_lap(laps, record)
                                record[f"sector{str(sc_no + 1)}_time"] = sc_value
                                last_record_ts = ts
                        
                        elif key_type == "PreviousValue":
                            if sc_no != 2:
                                record[f"sector{str(sc_no + 1)}_time"] = sc_value
                                last_record_ts = ts
                            elif len(laps) > 0:
                                laps[-1][f"sector{str(sc_no + 1)}_time"] = sc_value
                                last_record_ts = ts
                    
                

        laps_df = pd.DataFrame(laps)    
        laps_df["DriverNo"] = driver_no
        all_laps.append(laps_df)

    all_laps_df = pd.concat(all_laps, ignore_index=True)


    def delete_laps(laps_df, df_rcm):
        laps_df["isDeleted"] = False

        df_rcm_del = df_rcm[(df_rcm["Category"] == "Other") & (df_rcm.Message.str.split(" ").str[0] == "CAR")]
        df_rcm_del["deleted_driver"] = df_rcm_del.Message.str.split(" ").str[1]
        df_rcm_del["deleted_type"] = df_rcm_del.Message.str.split(" ").str[3]
        df_rcm_del["deleted_lap"] = df_rcm_del.apply(lambda x: x.Message.split(" ")[12] if x.deleted_type == "LAP" else x.Message.split(" ")[13] if x.deleted_type == "TIME" else None, axis=1)
        df_rcm_del["deleted_lap"] = df_rcm_del.apply(lambda x: x.Message.split(" ")[12] if x.deleted_type == "LAP" else x.Message.split(" ")[13] if x.deleted_type == "TIME" else None, axis=1)

        for idx, row in df_rcm_del.iterrows():
            try: int(row["deleted_lap"])
            except: continue
            row_bool = (laps_df["lap_number"] == int(row["deleted_lap"])) & (laps_df["DriverNo"] == row["deleted_driver"])
            laps_df.loc[row_bool, "isDeleted"] = True
            laps_df.loc[row_bool, "deletionMessage"] = row["Message"]

        return laps_df
    
    ## TODO: This is a temporary fix for the sector times.
    # segments = ["sector1_time", "sector2_time", "sector3_time"]
    # for idx in range(len(segments)):
    #     rest = np.delete(segments, idx)
    #     all_laps_df[segments[idx]] = (
    #         all_laps_df[segments[idx]].fillna(timedelta(minutes=0)) + (all_laps_df[segments[idx]].isnull() & (all_laps_df["lap_number"] > 1) & (~all_laps_df["lap_time"].isnull())) * (all_laps_df[segments[idx]].isnull() * (all_laps_df["lap_time"].fillna(timedelta(minutes=0)) - all_laps_df[rest].sum(axis=1)))).replace(timedelta(minutes=0), np.timedelta64("NaT"))

    new_ts = (all_laps_df["lap_start_time"] + all_laps_df["lap_time"]).shift(1)
    all_laps_df["lap_start_time"] = (new_ts.isnull() * all_laps_df["lap_start_time"]) + new_ts.fillna(timedelta(0))
    all_laps_df["lap_start_date"] = (all_laps_df["lap_start_time"] + bronze_lake.great_lake.session.first_datetime).fillna(bronze_lake.great_lake.session.session_start_datetime)

    all_laps_df = delete_laps(all_laps_df, df_rcm)

    return all_laps_df


def generate_car_telemetry_table(bronze_lake):
    session = bronze_lake.great_lake.session

    df_pos = bronze_lake.get("Position.z")
    df_pos["Utc"] = to_datetime(df_pos["Utc"])
    df_pos["timestamp"] = pd.to_timedelta(df_pos["timestamp"])

    df_car = bronze_lake.get("CarData.z")
    df_car["Utc"] = to_datetime(df_car["Utc"])
    df_car["timestamp"] = pd.to_timedelta(df_car["timestamp"])

    df = df_car.set_index(["DriverNo", "Utc"]).join(df_pos.set_index(["DriverNo", "Utc"]), rsuffix="_pos", how="outer").reset_index().sort_values(["DriverNo", "Utc"])

    all_drivers_data = []

    for driver_no in df["DriverNo"].unique():
        df_driver = df[df["DriverNo"] == driver_no].set_index("Utc")
        laps = session.laps
        laps_driver = laps[laps["DriverNo"] == driver_no]

        for col in df_driver.columns:
            if col in interpolation_map:
                df_driver[col] = df_driver[col].interpolate(method=interpolation_map[col], order=2).values

        # laps_driver["lap_end_date"] = laps_driver["lap_start_date"] + laps_driver["lap_time"] - timedelta(milliseconds=1)
        # laps_driver = pd.concat([laps_driver[["lap_start_date", "lap_number"]].set_index("lap_start_date"), laps_driver[["lap_end_date", "lap_number"]].set_index("lap_end_date")]).reset_index().sort_values("index").dropna()
        laps_driver.loc[:, "lap_end_date"] = laps_driver["lap_start_date"] + laps_driver["lap_time"]

        # df_driver = df_driver.join(laps_driver.set_index("index"), how="outer")
        df_driver = df_driver.join(laps_driver[["lap_start_date", "lap_number"]].set_index("lap_start_date"), how="outer")
        df_driver["lap_number"] = df_driver["lap_number"].ffill().bfill()
        df_driver.index.names = ['Utc']

        df_driver = df_driver.reset_index()
        # df_driver = df_driver[df_driver.Utc.between(laps_driver["index"].min(), laps_driver["index"].max())]
        df_driver = df_driver[df_driver.Utc.between(laps_driver["lap_start_date"].min(), laps_driver["lap_end_date"].max())]

        df_driver["SessionKey"] = df_driver["SessionKey"].ffill().bfill()
        df_driver["timestamp"] = df_driver["Utc"] - session.first_datetime

        all_drivers_data.append(df_driver)

    all_drivers_df = pd.concat(all_drivers_data, ignore_index=True)
    
    return all_drivers_df