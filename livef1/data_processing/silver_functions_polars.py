"""
Polars implementation of :mod:`livef1.data_processing.silver_functions`.

Used when the polars dataframe backend is configured::

    livef1.configure(dataframe_backend="polars")
    session = livef1.get_session(2026, "British", "Race")
    session.generate()
    session.laps                        # polars.DataFrame

The functions take the session's polars bronze tables (built by
:mod:`livef1.data_processing.bronze_polars`) and reproduce the pandas silver
functions with Polars expressions. The bronze DataFrames are never mutated.
"""
import re
from datetime import timedelta

import numpy as np
import polars as pl
from scipy.interpolate import interp1d

from ..utils.constants import (
    interpolation_map,
    silver_cartel_col_order,
    silver_laps_col_order,
    silver_race_control_messages_col_order,
    FIA_CATEGORY_SCOPE_RULES,
    penalty_types,
)
from .bronze_polars import utc_to_datetime as _utc_to_datetime, str_to_duration as _str_to_duration

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _select(df, columns=None):
    """Keep only ``columns`` of a bronze table (missing ones are ignored); categoricals become strings."""
    if df is None:
        return None
    if columns is not None:
        df = df.select([c for c in columns if c in df.columns])
    return df.with_columns(pl.col(pl.Categorical, pl.Enum).cast(pl.String))


def _dt_lit(value):
    """Session datetime (python datetime / numpy datetime64) -> polars datetime[ns] literal."""
    return pl.lit(value).cast(pl.Datetime("ns"))


def _gap_to_float(col):
    """
    GapToLeader / IntervalToPositionAhead parsing used by the laps state machine.

    null -> null (value absent, keep the previous one), "...LAP..." -> 0.0,
    "...L..." -> NaN (value present but explicitly reset to None), else float.
    """
    c = pl.col(col)
    return (
        pl.when(c.is_null()).then(None)
        .when(c.str.contains("LAP", literal=True)).then(0.0)
        .when(c.str.contains("L", literal=True)).then(float("nan"))
        .otherwise(c.cast(pl.Float64, strict=False))
        .alias(col)
    )


def _ensure_columns(df, cols, dtype=pl.String):
    missing = [c for c in cols if c not in df.columns]
    return df.with_columns([pl.lit(None, dtype).alias(c) for c in missing]) if missing else df


# ---------------------------------------------------------------------------
# Laps
# ---------------------------------------------------------------------------

def add_track_status(laps_df, df_trackstatus):
    start = laps_df["LapStartTime"].to_list()
    end = laps_df["LapStartTime"].shift(-1).to_list()

    # Missing lap ends are extrapolated from the previous lap end + lap interval (sequential, like pandas).
    for i in range(1, len(end)):
        if end[i] is None:
            prev, prev_start, curr_start = end[i - 1], start[i - 1], start[i]
            end[i] = None if None in (prev, prev_start, curr_start) else prev + (curr_start - prev_start)

    laps_df = laps_df.with_columns(pl.Series("LapEndTime", end, dtype=pl.Duration("us")))
    if laps_df["LapEndTime"].null_count() == laps_df.height:
        return laps_df.with_columns(pl.lit(None, pl.String).alias("TrackStatus"))

    # Outer merge on LapEndTime == timestamp, sorted, then LapNo backfilled:
    # every track status event belongs to the first lap ending at/after it.
    timeline = pl.concat([
        df_trackstatus.select(
            pl.col("timestamp").cast(pl.Duration("us")).alias("LapEndTime"),
            pl.lit(None, pl.Int64).alias("LapNo"),
            pl.col("Status").cast(pl.String),
            pl.lit(0).alias("_order"),
        ),
        laps_df.select(
            "LapEndTime",
            pl.col("LapNo").cast(pl.Int64),
            pl.lit(None, pl.String).alias("Status"),
            pl.lit(1).alias("_order"),
        ),
    ]).sort(["LapEndTime", "_order"], nulls_last=True, maintain_order=True)

    status_df = (
        timeline
        .with_columns(pl.col("LapNo").backward_fill())
        .drop_nulls("LapNo")
        .group_by("LapNo")
        .agg(pl.col("Status").drop_nulls().unique().sort().str.join(",").alias("TrackStatus"))
        .with_columns(pl.col("TrackStatus").replace("", "1"))
    )
    return laps_df.join(status_df, on="LapNo", how="left", maintain_order="left")


def delete_laps(laps_df, df_rcm):
    tokens = pl.col("Message").str.split(" ")
    df_rcm_del = (
        df_rcm
        .filter((pl.col("Category") == "Other") & (tokens.list.get(0, null_on_oob=True) == "CAR"))
        .select(
            "Message",
            tokens.list.get(1, null_on_oob=True).alias("deleted_driver"),
            tokens.list.get(3, null_on_oob=True).alias("deleted_type"),
            tokens.list.len().alias("_n_tokens"),
            tokens.alias("_tokens"),
        )
        .with_columns(
            pl.when(pl.col("deleted_type") == "TIME")
            .then(pl.col("_tokens").list.get(4, null_on_oob=True))
            .alias("deleted_time")
        )
    )

    # Drop deletions that were later reinstated (and the reinstatement message itself)
    reinstated = df_rcm_del.filter(
        pl.col("Message").str.contains("REINSTATED", literal=True) & (pl.col("deleted_type") == "TIME")
    ).select("deleted_driver", "deleted_time").unique()
    df_rcm_del = df_rcm_del.join(reinstated, on=["deleted_driver", "deleted_time"], how="anti", maintain_order="left")

    laps_df = laps_df.with_columns(pl.lit(False).alias("IsDeleted"))
    if df_rcm_del.height == 0:
        return laps_df

    deletions = (
        df_rcm_del
        .with_columns(
            pl.when(pl.col("_n_tokens") > 12)
            .then(
                pl.when(pl.col("deleted_type") == "LAP").then(pl.col("_tokens").list.get(12, null_on_oob=True))
                .when(pl.col("deleted_type") == "TIME").then(pl.col("_tokens").list.get(13, null_on_oob=True))
            )
            .cast(pl.Int64, strict=False)
            .alias("LapNo")
        )
        .drop_nulls("LapNo")
        .select(pl.col("deleted_driver").alias("DriverNo"), "LapNo", pl.col("Message").alias("DeletionMessage"))
        .unique(subset=["DriverNo", "LapNo"], keep="last", maintain_order=True)
    )
    if deletions.height == 0:
        return laps_df

    return (
        laps_df
        .join(deletions.with_columns(pl.lit(True).alias("_deleted_hit")), on=["DriverNo", "LapNo"], how="left", maintain_order="left")
        .with_columns(pl.col("_deleted_hit").fill_null(False).alias("IsDeleted"))
        .drop("_deleted_hit")
    )


def generate_laps_table(session, df_exp, df_rcm, df_tyre, df_track):

    df_exp = _select(df_exp, [
        "SessionKey", "DriverNo", "timestamp", "RacingNumber", "Stopped", "InPit", "PitOut", "LastLapTime_Value",
        "Sectors_0_Value", "Sectors_1_Value", "Sectors_2_Value",
        "Sectors_0_PreviousValue", "Sectors_1_PreviousValue", "Sectors_2_PreviousValue",
        "Speeds_I1_Value", "Speeds_I2_Value", "Speeds_FL_Value", "Speeds_ST_Value",
        "Position", "GapToLeader", "IntervalToPositionAhead_Value",
    ])
    df_rcm = _select(df_rcm, ["Category", "Message"])
    df_tyre = _select(df_tyre)
    df_track = _select(df_track)

    session_key = df_exp["SessionKey"][0]

    sector_value_cols = ["Sectors_0_Value", "Sectors_1_Value", "Sectors_2_Value"]
    sector_prev_cols = ["Sectors_0_PreviousValue", "Sectors_1_PreviousValue", "Sectors_2_PreviousValue"]
    speedTrap_cols = {
        "Speeds_I1_Value": "Speed_I1",
        "Speeds_I2_Value": "Speed_I2",
        "Speeds_FL_Value": "Speed_FL",
        "Speeds_ST_Value": "Speed_ST",
    }
    misc_cols = {"Position": "Position"}
    if session.type == "Race":
        misc_cols["GapToLeader"] = "GapToLeader"
        misc_cols["IntervalToPositionAhead_Value"] = "IntervalToPositionAhead"

    # Record columns and their dtypes (the pandas `cols`, minus the `None` keys)
    lap_schema = {
        "LapNo": pl.Int64,
        "LapTime": pl.Duration("us"),
        "PitIn": pl.Duration("us"),
        "PitOut": pl.Duration("us"),
        "Sector1_Time": pl.Duration("us"),
        "Sector2_Time": pl.Duration("us"),
        "Sector3_Time": pl.Duration("us"),
        **{v: pl.Float64 for v in speedTrap_cols.values()},
        **{v: (pl.String if k == "Position" else pl.Float64) for k, v in misc_cols.items()},
        "NoPits": pl.Int64,
        "LapStartTime": pl.Duration("us"),
    }
    cols = [c for c in lap_schema if c not in ("NoPits", "LapStartTime")]

    # Columns visited by the state machine, in the same order as the pandas row iteration
    loop_cols = ["InPit", "PitOut"] + sector_value_cols + sector_prev_cols + list(speedTrap_cols) + list(misc_cols)

    # Vectorised preprocessing: '' -> null, then parse timings / speeds / gaps once for all drivers
    df_test = (
        _ensure_columns(df_exp, ["LastLapTime_Value", "RacingNumber", "Stopped", "InPit", "PitOut"]
                        + sector_value_cols + sector_prev_cols + list(speedTrap_cols) + list(misc_cols))
        .select(["DriverNo", "timestamp", "LastLapTime_Value", "RacingNumber", "Stopped"] + loop_cols)
        .with_columns(pl.when(pl.col(pl.String) == "").then(None).otherwise(pl.col(pl.String)).name.keep())
        .filter(pl.col("RacingNumber").is_null())
        .with_columns(
            [_str_to_duration(c) for c in sector_value_cols + sector_prev_cols + ["LastLapTime_Value"]]
            + [pl.col(c).cast(pl.Float64, strict=False) for c in speedTrap_cols]
            + [_gap_to_float(c) for c in misc_cols if c != "Position"]
            + [pl.col("timestamp").cast(pl.Duration("us"))]
        )
    )

    def new_record(prev=None):
        if prev is None:
            record = {key: None for key in cols}
            record["LapNo"], record["NoPits"] = 1, 0
            return record
        record = {key: None for key in prev}
        record["LapNo"] = prev["LapNo"] + 1
        record["NoPits"] = prev["NoPits"]
        record["Position"] = prev["Position"]
        return record

    def close_lap(laps, record):
        if record["LapTime"] is None and None not in (record["Sector1_Time"], record["Sector2_Time"], record["Sector3_Time"]):
            record["LapTime"] = record["Sector1_Time"] + record["Sector2_Time"] + record["Sector3_Time"]
        laps.append(record)
        return new_record(record)

    all_laps = []

    for (driver_no,), df_driver in df_test.partition_by("DriverNo", as_dict=True, maintain_order=True).items():
        laps, record = [], new_record()
        last_record_ts = timedelta(seconds=0)

        for row in df_driver.iter_rows(named=True):
            ts = row["timestamp"]

            if row["Stopped"] == True:
                record = close_lap(laps, record)
                continue

            if row["LastLapTime_Value"] is not None:
                if row["Sectors_2_Value"] is not None:
                    record["LapTime"] = row["LastLapTime_Value"]
                elif row["Sectors_2_PreviousValue"] is not None and laps:
                    laps[-1]["LapTime"] = row["LastLapTime_Value"]

            for sc_key in loop_cols:
                sc_value = row[sc_key]
                if sc_value is None:
                    continue

                if sc_key in speedTrap_cols:
                    record[speedTrap_cols[sc_key]] = sc_value

                elif sc_key == "InPit":
                    if sc_value == 1:
                        record["PitIn"] = ts
                elif sc_key == "PitOut":
                    if sc_value == True:
                        record["PitOut"] = ts
                        record["NoPits"] += 1

                elif sc_key == "Position":
                    record["Position"] = sc_value
                elif sc_key in misc_cols:
                    record[misc_cols[sc_key]] = None if sc_value != sc_value else sc_value  # NaN -> explicit reset

                else:
                    _, sc_no, key_type = sc_key.split("_")
                    sector_col = f"Sector{int(sc_no) + 1}_Time"

                    if key_type == "Value":
                        if record[sector_col] is None:
                            record[sector_col] = sc_value
                            last_record_ts = ts
                            if sc_no == "2":
                                record = close_lap(laps, record)
                                record["LapStartTime"] = ts
                        elif sc_value == record[sector_col]:
                            pass
                        elif ts - last_record_ts > timedelta(seconds=10):
                            record = close_lap(laps, record)
                            record[sector_col] = sc_value
                            record["LapStartTime"] = ts - sc_value
                            last_record_ts = ts

                    elif key_type == "PreviousValue":
                        if sc_no != "2":
                            record[sector_col] = sc_value
                            last_record_ts = ts
                        elif laps:
                            laps[-1][sector_col] = sc_value
                            last_record_ts = ts

        if not laps:
            continue

        laps_df = (
            pl.DataFrame(laps, schema=lap_schema)
            .with_columns(pl.lit(driver_no).alias("DriverNo"))
            # Lap start = previous lap start + previous lap time, otherwise the recorded start
            .with_columns((pl.col("LapStartTime") + pl.col("LapTime")).shift(1).fill_null(pl.col("LapStartTime")).alias("LapStartTime"))
        )
        all_laps.append(add_track_status(laps_df, df_track))

    all_laps_df = pl.concat(all_laps, how="diagonal_relaxed")
    all_laps_df = all_laps_df.with_columns(
        (pl.col("LapStartTime").cast(pl.Duration("ns")) + _dt_lit(session.first_datetime)).fill_null(_dt_lit(session.session_start_datetime)).alias("LapStartDate")
    )
    if all_laps_df.height > 1:
        r0, r1 = all_laps_df.row(0, named=True), all_laps_df.row(1, named=True)
        fill = None if r1["LapStartTime"] is None else r1["LapStartTime"] - (r1["LapStartDate"] - r0["LapStartDate"])
        all_laps_df = all_laps_df.with_columns(pl.col("LapStartTime").fill_null(pl.lit(fill, pl.Duration("us"))))

    # Fill position data with timing data (first non-null Position per driver from the RacingNumber rows)
    first_pos = (
        df_exp.filter(pl.col("RacingNumber").is_not_null())
        .sort("timestamp", maintain_order=True)
        .group_by("DriverNo", maintain_order=True)
        .agg(pl.col("Position").drop_nulls().first().alias("_first_pos"))
    )
    all_laps_df = (
        all_laps_df.join(first_pos, on="DriverNo", how="left", maintain_order="left")
        .with_columns(
            pl.when((pl.col("LapNo") == 1) & pl.col("Position").is_null())
            .then(pl.col("_first_pos")).otherwise(pl.col("Position")).alias("Position")
        )
        .drop("_first_pos")
    )

    # Delete laps
    all_laps_df = delete_laps(all_laps_df, df_rcm)

    # Add session data
    all_laps_df = all_laps_df.with_columns(pl.lit(session_key).alias("SessionKey"))

    # Add pit data
    if "PitStopSeries" in session.topic_names_info:
        df_pit = _select(session.get_data("PitStopSeries", level="bronze")).select(
            pl.col("RacingNumber").alias("DriverNo"),
            "Utc",
            pl.col("PitStopTime").alias("PitStopDuration"),
            pl.col("PitLaneTime").alias("PitLaneDuration"),
            pl.col("Lap").cast(pl.String).alias("LapNo"),
        ).with_row_index("_pit_idx")
        df_pit = _utc_to_datetime(df_pit)

        # Where LapNo is missing or empty, infer from pit time vs lap start times
        missing = df_pit.filter(pl.col("LapNo").is_null() | (pl.col("LapNo").str.strip_chars() == ""))
        if missing.height:
            inferred = (
                missing.drop_nulls("Utc").select("_pit_idx", "DriverNo", "Utc")
                .join(all_laps_df.drop_nulls("LapStartDate").select("DriverNo", "LapStartDate", "LapNo"), on="DriverNo")
                .filter(pl.col("LapStartDate") <= pl.col("Utc"))
                .group_by("_pit_idx")
                .agg(pl.col("LapNo").get(pl.col("LapStartDate").arg_max()).cast(pl.String).alias("_lap"))
            )
            df_pit = (
                df_pit.join(inferred, on="_pit_idx", how="left", maintain_order="left")
                .with_columns(pl.coalesce("_lap", "LapNo").alias("LapNo"))
                .drop("_lap")
            )

        df_pit = df_pit.drop("Utc", "_pit_idx").with_columns(
            pl.col("LapNo").cast(pl.Float64, strict=False).fill_null(-1).cast(pl.Int64)
        )
        all_laps_df = all_laps_df.join(df_pit, on=["DriverNo", "LapNo"], how="left", maintain_order="left")

    # Add tyre data: union of laps and tyre events sorted by (DriverNo, LapEndTime), then forward-filled per driver
    tyre_cols = ["Compound", "New", "TyreAge"]
    # A lap without LapTime (e.g. lap 1) ends when the driver's next lap starts; without a next lap, use its own start
    all_laps_df = all_laps_df.sort(["DriverNo", "LapNo"], maintain_order=True).with_columns(
        (pl.col("LapStartTime") + pl.col("LapTime"))
        .fill_null(pl.col("LapStartTime").shift(-1).over("DriverNo"))
        .fill_null(pl.col("LapStartTime"))
        .alias("LapEndTime")
    )
    tyre = df_tyre.select(
        "DriverNo",
        pl.col("timestamp").cast(pl.Duration("us")).alias("LapEndTime"),
        "Compound", "New",
        pl.col("TotalLaps").cast(pl.Float64).alias("TyreAge"),
    )
    all_laps_df = (
        pl.concat([tyre.with_columns(pl.lit(0).alias("_order")), all_laps_df.with_columns(pl.lit(1).alias("_order"))], how="diagonal_relaxed")
        .sort(["DriverNo", "LapEndTime", "_order"], nulls_last=True, maintain_order=True)
        .with_columns(pl.col(tyre_cols).forward_fill().over("DriverNo"))
        .filter(pl.col("_order") == 1)
        .drop("_order")
        .drop_nulls("SessionKey")
    )

    all_laps_df = _ensure_columns(all_laps_df, [c for c in silver_laps_col_order if c != "Driver"])
    all_laps_df = all_laps_df.select([c for c in silver_laps_col_order if c != "Driver"]).sort(["DriverNo", "LapNo"], maintain_order=True)

    # Add driver data (Driver objects, same as the pandas table)
    return all_laps_df.with_columns(
        pl.Series("Driver", [session.drivers.get(d) for d in all_laps_df["DriverNo"]], dtype=pl.Object)
    )


# ---------------------------------------------------------------------------
# Car telemetry
# ---------------------------------------------------------------------------

def _interpolate_quadratic(x, y):
    """pandas ``interpolate(method="quadratic")``: scipy interp1d on the index, leading/trailing NaN kept."""
    y = y.astype(np.float64)
    valid = ~np.isnan(y)
    if valid.all() or valid.sum() < 3:
        return y
    out = y.copy()
    out[~valid] = interp1d(x[valid], y[valid], kind="quadratic", fill_value=np.nan, bounds_error=False)(x[~valid])
    first, last = np.argmax(valid), len(valid) - np.argmax(valid[::-1])
    out[:first] = np.nan
    out[last:] = np.nan
    return out


def interpolate_driver(df_driver):
    """Per-driver interpolation following ``interpolation_map`` (skips columns that are < 20% filled)."""
    exprs = []
    x = None
    for col, method in interpolation_map.items():
        if col not in df_driver.columns or df_driver[col].count() < df_driver.height * 0.2:
            continue
        c = pl.col(col)
        if method == "ffill":
            exprs.append(c.forward_fill())
        elif method == "linear":
            # pandas linear interpolation also fills trailing NaN with the last value
            exprs.append(c.interpolate().forward_fill())
        elif method == "index":
            exprs.append(c.interpolate_by("Utc").forward_fill())
        elif method in ("quadratic", "polynomial"):
            if x is None:
                x = df_driver["Utc"].cast(pl.Int64).to_numpy().astype(np.float64)
            values = _interpolate_quadratic(x, df_driver[col].cast(pl.Float64).to_numpy())
            exprs.append(pl.Series(col, values).cast(df_driver.schema[col]))
    return df_driver.with_columns(exprs) if exprs else df_driver


def add_distance_to_lap(df_driver, start_x, start_y, x_coeff, y_coeff):
    """Vectorised ``add_distance_to_lap`` applied to every lap of a driver at once."""
    dt = pl.col("timestamp").diff().dt.total_microseconds().fill_null(0) / 1e6
    lap_distance = (((pl.col("Speed") + pl.col("Speed").shift(1)) / 2 / 3.6) * dt).cum_sum()

    x0, y0 = pl.col("X").first(), pl.col("Y").first()
    direction = pl.when(((x0 - start_x) / x_coeff > 0) & ((y0 - start_y) / y_coeff > 0)).then(1).otherwise(-1)
    offset = direction * ((x0 - start_x) ** 2 + (y0 - start_y) ** 2).sqrt() / 10

    return df_driver.with_columns((offset + lap_distance).over("LapNo").alias("Distance"))


def add_track_status_telemetry(telemetry_df, df_track):
    return (
        telemetry_df
        .join(df_track.select("timestamp", pl.col("Status").cast(pl.String).alias("TrackStatus"))
              .unique("timestamp", keep="last", maintain_order=True),
              on="timestamp", how="left", maintain_order="left")
        .with_columns(pl.col("TrackStatus").forward_fill())
        .drop_nulls("SessionKey")
    )


def add_lineposition(telemetry_df, df_tmg):
    # Outer join + ffill on the timing rows == latest non-null timing Position at/before each sample
    positions = df_tmg.select("timestamp", "Position").drop_nulls("Position").sort("timestamp", maintain_order=True)
    return telemetry_df.sort("timestamp", maintain_order=True).join_asof(positions, on="timestamp", strategy="backward")


def add_interval_to_position_ahead(telemetry_df, df_tmg):
    # Same filter as pandas: nulls are kept (str.contains on NA -> False), laps behind and '' are dropped
    temp_tmg = (
        df_tmg.select("timestamp", "IntervalToPositionAhead_Value")
        .filter(
            ~pl.col("IntervalToPositionAhead_Value").str.contains("L", literal=True).fill_null(False)
            & (pl.col("IntervalToPositionAhead_Value") != "").fill_null(True)
        )
        .sort("timestamp", maintain_order=True)
    )
    return (
        telemetry_df.join_asof(temp_tmg, on="timestamp", strategy="backward")
        .with_columns(pl.col("IntervalToPositionAhead_Value").cast(pl.Float64).alias("IntervalToPositionAhead"))
        .drop("IntervalToPositionAhead_Value")
    )


def assign_regions(df_corners):
    """``np.select`` over track regions as a when/then chain (first match wins, default None)."""
    expr = pl.lit(None, pl.String)
    distance = pl.col("Distance")
    for row in reversed(list(df_corners.iter_rows(named=True))):
        if row["corner_end"] >= row["corner_start"]:
            cond = (distance >= row["corner_start"]) & (distance < row["corner_end"])
        else:
            cond = (distance >= row["corner_start"]) | (distance < row["corner_end"])
        expr = pl.when(cond).then(pl.lit(row["name"])).otherwise(expr)
    return expr.alias("TrackRegion")


def generate_car_telemetry_table(session, df_car, df_pos, df_tyre, laps, df_track, df_tmg, df_circuits):
    """
    Polars twin of ``silver_functions.generate_car_telemetry_table``.

    ``laps`` must be the Polars laps table produced by :func:`generate_laps_table`.
    """
    # Only the columns the silver table uses are converted (bronze `timestamp` is recomputed from Utc)
    df_car = _utc_to_datetime(_select(df_car, ["SessionKey", "DriverNo", "Utc", "RPM", "Speed", "GearNo", "Throttle", "Brake", "DRS"]))
    df_pos = _utc_to_datetime(_select(df_pos, ["DriverNo", "Utc", "Status", "X", "Y", "Z"]))
    df_tyre = _select(df_tyre, ["DriverNo", "timestamp", "Compound", "New", "TotalLaps"]).with_columns(pl.col("timestamp").cast(pl.Duration("ns")))
    df_tmg = _select(df_tmg, ["DriverNo", "timestamp", "Position", "IntervalToPositionAhead_Value"]).with_columns(pl.col("timestamp").cast(pl.Duration("ns")))
    df_track = _select(df_track, ["timestamp", "Status"]).with_columns(pl.col("timestamp").cast(pl.Duration("ns")))
    df_circuits = _select(df_circuits)
    first_datetime = _dt_lit(session.first_datetime)
    circuit = session.meeting.circuit
    has_start = hasattr(circuit, "start_coordinates")

    tmg_has_interval = "IntervalToPositionAhead_Value" in df_tmg.columns
    tmg_by_driver = df_tmg.partition_by("DriverNo", as_dict=True)
    empty_tmg = df_tmg.clear()

    # Tyre events forward-filled per driver: an as-of join on them equals the pandas outer join + ffill
    tyre_by_driver = (
        df_tyre.select("DriverNo", "timestamp", "Compound", "New", pl.col("TotalLaps").cast(pl.Float64).alias("TyreAge"))
        .sort(["DriverNo", "timestamp"], maintain_order=True)
        .with_columns(pl.col("Compound", "New", "TyreAge").forward_fill().over("DriverNo"))
        .partition_by("DriverNo", as_dict=True, include_key=False)
    )
    empty_tyre = pl.DataFrame(schema={"timestamp": pl.Duration("ns"), "Compound": pl.String, "New": pl.String, "TyreAge": pl.Float64})

    # Car and position data are joined driver by driver (in sorted DriverNo order, like the pandas
    # global sort) so only one driver's joined samples are in memory at a time.
    car_by_driver = df_car.with_columns(pl.lit(True).alias("_car")).partition_by("DriverNo", as_dict=True)
    pos_by_driver = df_pos.with_columns(pl.lit(True).alias("_pos")).partition_by("DriverNo", as_dict=True)
    del df_car, df_pos
    empty_car = pl.DataFrame(schema=next(iter(car_by_driver.values())).schema) if car_by_driver else None
    empty_pos = pl.DataFrame(schema=next(iter(pos_by_driver.values())).schema) if pos_by_driver else None

    last_car_status = None
    all_drivers_data = []
    for key in sorted(set(car_by_driver) | set(pos_by_driver)):
        driver_no = key[0]
        df_driver = (
            car_by_driver.pop(key, empty_car)
            .join(pos_by_driver.pop(key, empty_pos), on=["DriverNo", "Utc"], how="full", coalesce=True)
            .sort("Utc", maintain_order=True)
            .rename({"Status": "CarStatus"})
            .with_columns(
                # pandas forward-fills CarStatus over all drivers at once, so it carries across drivers
                pl.col("CarStatus").forward_fill().fill_null(pl.lit(last_car_status, pl.String)),
                (pl.when(pl.col("_car")).then(pl.lit("car")).otherwise(pl.lit(""))
                 + pl.when(pl.col("_pos")).then(pl.lit("position")).otherwise(pl.lit(""))).alias("tag"),
            )
            .drop("_car", "_pos")
        )
        if df_driver.height:
            last_car_status = df_driver["CarStatus"][-1]

        laps_driver = (
            laps.filter(pl.col("DriverNo") == driver_no)
            .select("LapNo", "LapStartDate", (pl.col("LapStartDate") + pl.col("LapTime")).alias("lap_end_date"))
        )

        df_driver = interpolate_driver(df_driver)

        # Lap number = lap with the latest start at/before the sample, restricted to the laps window
        df_driver = (
            df_driver.join_asof(
                laps_driver.select("LapStartDate", pl.col("LapNo").cast(pl.Float64))
                .drop_nulls("LapStartDate").sort("LapStartDate", maintain_order=True),
                left_on="Utc", right_on="LapStartDate", strategy="backward",
            )
            .drop("LapStartDate")
            .filter(pl.col("Utc").is_between(laps_driver["LapStartDate"].min(), laps_driver["lap_end_date"].max()))
            .with_columns(
                pl.col("SessionKey").forward_fill().backward_fill(),
                (pl.col("Utc") - first_datetime).alias("timestamp"),
            )
        )

        if has_start:
            df_driver = add_distance_to_lap(
                df_driver,
                circuit.start_coordinates[0],
                circuit.start_coordinates[1],
                circuit.start_direction[0],
                circuit.start_direction[1],
            )
        else:
            df_driver = df_driver.with_columns(pl.lit(None, pl.Float64).alias("Distance"))

        tmg_driver = tmg_by_driver.get((driver_no,), empty_tmg)
        df_driver = add_track_status_telemetry(df_driver, df_track)
        df_driver = add_lineposition(df_driver, tmg_driver)
        if tmg_has_interval:
            df_driver = add_interval_to_position_ahead(df_driver, tmg_driver)

        # Add tyre data
        df_driver = df_driver.join_asof(tyre_by_driver.get((driver_no,), empty_tyre), on="timestamp", strategy="backward")

        if df_circuits is not None and has_start:
            df_driver = df_driver.with_columns(assign_regions(df_circuits))
        else:
            df_driver = df_driver.with_columns(pl.lit(None, pl.String).alias("TrackRegion"))

        all_drivers_data.append(df_driver.select([c for c in silver_cartel_col_order if c in df_driver.columns]))

    # rechunk=False: the per-driver chunks are referenced, not copied into a new buffer
    return pl.concat(all_drivers_data, how="diagonal_relaxed", rechunk=False)


# ---------------------------------------------------------------------------
# Race control messages
# ---------------------------------------------------------------------------

def _is_valid_car_number(num_str, context_before, context_after):
    """True if a number next to CAR is not a lap / turn / timestamp / lap time."""
    text = context_before + num_str + context_after
    if re.search(r'\d+\s*:\s*' + re.escape(num_str) + r'\s*:\s*\d+', text):
        return False
    if re.search(re.escape(num_str) + r'\s*:\s*\d+', context_after):
        return False
    if re.search(r'LAP\s+' + re.escape(num_str) + r'\b', text, re.IGNORECASE):
        return False
    if re.search(r'TURN\s+' + re.escape(num_str) + r'\b', text, re.IGNORECASE):
        return False
    if re.search(r'\d+\s*:\s*' + re.escape(num_str) + r'\s*\.\s*\d+', text):
        return False
    return True


def parse_cars_from_message(message):
    """
    Same parsing as the pandas pipeline. Kept as a Python UDF because the
    patterns rely on look-arounds, which the Polars (Rust) regex engine lacks.
    """
    if message is None or not message:
        return None

    cars = []
    message_upper = message.upper()

    # Case 1: "CAR 23 (ALB) ..."
    if re.search(r'\bCAR\s+', message_upper) and not re.search(r'\bCARS\s+', message_upper):
        for match in re.finditer(r'(?i)\bCAR\s+(\d+)', message):
            car_num = match.group(1)
            context_before = message[max(0, match.start() - 30):match.start()]
            context_after = message[match.end():min(len(message), match.end() + 30)]
            if _is_valid_car_number(car_num, context_before, context_after):
                cars.append(int(car_num))

    # Case 2: "CARS 44 (HAM) AND 18 (STR) ..."
    elif re.search(r'\bCARS\s+', message_upper):
        cars_pattern = r'(?i)\bCARS\s+((?:\d+\s*\([^)]+\)(?:\s*,\s*|\s+AND\s+)?)+?)(?=\s+(?:NOTED|WILL|REVIEWED|NO|FIA|$))'
        cars_match = re.search(cars_pattern, message)
        if cars_match:
            cars.extend(int(n) for n in re.findall(r'(\d+)\s*\([^)]+\)', cars_match.group(1)))
        else:
            cars_match = re.search(r'(?i)\bCARS\s+((?:\d+\s*\([^)]+\)(?:\s*,\s*|\s+AND\s+)?)+)', message)
            if cars_match and len(cars_match.group(1)) < 200:
                cars.extend(int(n) for n in re.findall(r'(\d+)\s*\([^)]+\)', cars_match.group(1)))

    unique_cars = list(dict.fromkeys(cars))
    return unique_cars if unique_cars else None


def _category_scope_exprs(columns):
    """Vectorised ``parse_category_scope``: returns (Category, Scope, Status, info) expressions."""
    message = pl.col("Message").str.to_uppercase()
    category, scope, flag = pl.col("Category"), pl.col("Scope"), pl.col("Flag")
    mode = pl.col("Mode") if "Mode" in columns else pl.lit(None, pl.String)
    status = pl.col("Status").cast(pl.String) if "Status" in columns else pl.lit(None, pl.String)
    null = pl.lit(None, pl.String)

    def last_after(expr, sep):
        return expr.str.split(sep).list.last().str.strip_chars()

    # Flag
    def clean_driver_flag(flag_name):
        return (
            message.str.replace_all(flag_name, "", literal=True)
            .str.replace_all("WAVED", "", literal=True)
            .str.replace_all("FLAG", "", literal=True)
            .str.replace_all("FOR", "", literal=True)
            .str.strip_chars()
        )

    flag_info = (
        pl.when((scope == "Driver") & (flag == "BLUE")).then(clean_driver_flag("BLUE").str.split(" ").list.last())
        .when((scope == "Driver") & (flag == "BLACK AND WHITE")).then(last_after(clean_driver_flag("BLACK AND WHITE"), "-"))
        .when(scope == "Sector").then(pl.lit("SECTOR ") + last_after(message, "SECTOR"))
        .when(scope == "Track").then(last_after(message, "-"))
        .otherwise(null)
    )

    # Other: first matching FIA rule wins
    rules = [(cat, sc, kws) for cat, scopes in FIA_CATEGORY_SCOPE_RULES.items() for sc, kws in scopes.items()]
    penalty_type = null
    for pt in reversed(penalty_types):
        penalty_type = pl.when(message.str.contains(pt, literal=True)).then(pl.lit(pt)).otherwise(penalty_type)
    penalty_value = pl.when(penalty_type == "TIME PENALTY").then(message.str.extract(r'(\d{1,2})\s*SECOND', 1)).otherwise(null)
    penalty_status = pl.when(message.str.contains("PENALTY SERVED", literal=True)).then(pl.lit("Served")).otherwise(null)
    dash_info = pl.when(message.str.contains("-", literal=True)).then(last_after(message, "-")).otherwise(null)

    # No FIA rule matched the message
    other = {"Category": pl.lit("Other"), "Scope": pl.lit("Unclassified"), "Status": null, "info": null}
    for cat, sc, kws in reversed(rules):
        matched = message.str.contains_any(kws)
        values = {
            "Category": pl.lit(cat),
            "Scope": pl.lit(sc),
            "Status": penalty_status if cat == "Penalty" else status,
            "info": penalty_value if cat == "Penalty" else dash_info,
        }
        other = {k: pl.when(matched).then(values[k]).otherwise(other[k]) for k in other}

    branches = {
        "Category": (category, category, category, other["Category"], pl.lit("Other")),
        "Scope": (scope, last_after(message, " "), mode, other["Scope"], pl.lit("Unclassified")),
        "Status": (status, status, status, other["Status"], null),
        "info": (flag_info, null, status, other["info"], null),
    }
    exprs = []
    for name, (flag_v, drs_v, sc_v, other_v, else_v) in branches.items():
        exprs.append(
            pl.when(category == "Flag").then(flag_v)
            .when(category == "Drs").then(drs_v)
            .when(category == "SafetyCar").then(sc_v)
            .when(category == "Other").then(other_v)
            .otherwise(else_v)
            .alias(name)
        )
    return exprs


def generate_race_control_messages_table(session, rcm_df):
    rcm = _select(rcm_df)
    rcm = rcm.with_columns(
        pl.col("Message").map_elements(parse_cars_from_message, return_dtype=pl.List(pl.Int64), skip_nulls=True).alias("RacingNumber")
    ).with_columns(_category_scope_exprs(rcm.columns))
    return rcm.select([c for c in silver_race_control_messages_col_order if c in rcm.columns])
