"""
Bronze layer of the polars dataframe backend.

Builds bronze tables directly from the parsed livetiming records as
``polars.DataFrame`` (no pandas involved), applying the same column renames,
dtype downcasts and timestamp parsing as the pandas ``BronzeTable``. Also holds
the session-level helpers that read bronze tables (first datetime, session start)
and the track regions built from the circuit's raw JSON.
"""
import polars as pl

from ..utils.constants import column_mapping, _DOWNCAST_MAP

_POLARS_DTYPES = {
    "float32": pl.Float32,
    "float64": pl.Float64,
    "uint8": pl.UInt8,
    "int64": pl.Int64,
}


def utc_to_datetime(df, col="Utc"):
    """Polars version of ``helper.to_datetime``: ISO8601 -> naive UTC, rounded half-to-even to ms."""
    if df.schema[col] == pl.String:
        ts = pl.col(col).str.strip_suffix("Z").str.to_datetime("%Y-%m-%dT%H:%M:%S%.f", time_unit="ns")
    else:
        ts = pl.col(col).cast(pl.Datetime("ns"))
    ns = ts.cast(pl.Int64)
    q, r = ns // 1_000_000, ns % 1_000_000
    round_up = (r > 500_000) | ((r == 500_000) & (q % 2 == 1))
    return df.with_columns(((q + round_up.cast(pl.Int64)) * 1_000_000).cast(pl.Datetime("ns")).alias(col))


def str_to_duration(col):
    """'1:23.456' / '23.456' / 'HH:MM:SS.fff' / 'D.HH:MM:SS.fff' -> Duration[us] (mirror of the pandas parsing)."""
    c = pl.col(col)
    days = c.str.extract(r"^(\d+)\.\d+:", 1).cast(pl.Float64, strict=False).fill_null(0.0)
    parts = c.str.replace(r"^\d+\.(\d+:)", "$1").str.split(":")
    n = parts.list.len()
    sec = parts.list.get(-1, null_on_oob=True).cast(pl.Float64, strict=False)
    mins = pl.when(n >= 2).then(parts.list.get(-2, null_on_oob=True).cast(pl.Float64, strict=False)).otherwise(0.0)
    hrs = pl.when(n >= 3).then(parts.list.get(-3, null_on_oob=True).cast(pl.Float64, strict=False)).otherwise(0.0)
    total_us = ((days * 86400 + hrs * 3600 + mins * 60 + sec) * 1e6).round()
    return total_us.cast(pl.Int64).cast(pl.Duration("us")).alias(col)


def build_bronze_frame(parsed_data):
    """Polars twin of ``BronzeTable``'s DataFrame: rename, downcast, parse ``timestamp``."""
    if isinstance(parsed_data, pl.DataFrame):
        df = parsed_data
    else:
        df = pl.from_dicts(list(parsed_data), infer_schema_length=None)

    df = df.rename({k: v for k, v in column_mapping.items() if k in df.columns})
    df = df.with_columns(
        # Columns that are always empty are typed as strings, like pandas object columns
        [pl.col(c).cast(pl.String) for c, dtype in df.schema.items() if dtype == pl.Null]
        + [pl.col(c).cast(_POLARS_DTYPES[dtype], strict=False) for c, dtype in _DOWNCAST_MAP.items() if c in df.columns]
    )
    if "timestamp" in df.columns and df.schema["timestamp"] == pl.String:
        df = df.with_columns(str_to_duration("timestamp"))
    return df


def build_track_regions(raw_circuit_data):
    """Polars twin of ``Circuit._load_circuit_data``'s track regions (corners, then straights)."""
    corners = pl.DataFrame(
        [
            {
                "number": c["number"],
                "angle": c.get("angle"),
                "Distance": c["length"],
                "X": c.get("trackPosition", c).get("x"),
                "Y": c.get("trackPosition", c).get("y"),
            }
            for c in raw_circuit_data["corners"]
        ],
        schema={"number": pl.Int64, "angle": pl.Float64, "Distance": pl.Float64, "X": pl.Float64, "Y": pl.Float64},
    ).with_columns(pl.col("Distance") / 10)

    next_start = (pl.col("Distance") - 50).shift(-1)
    end = pl.col("Distance") + 50
    corners = corners.with_columns(
        (pl.col("Distance") - 50).alias("corner_start"),
        # A corner ends where the next one starts when they overlap (same formula as pandas)
        ((end > next_start.fill_null(1_000_000)).cast(pl.Float64) * next_start.fill_null(0)
         + (end < next_start.fill_null(1_000_000)).cast(pl.Float64) * end).alias("corner_end"),
        (pl.lit("T") + pl.col("number").cast(pl.String)).alias("name"),
        pl.lit("Corner").alias("type"),
    ).select(["type", "name", "number", "X", "Y", "corner_start", "corner_end", "angle", "Distance"])

    straights = corners.select(
        pl.col("corner_end").shift(1).fill_null(pl.col("corner_end").max()).alias("corner_start"),
        pl.col("corner_start").alias("corner_end"),
        pl.col("number").shift(1).fill_null(0).cast(pl.Int64).alias("number"),
    ).with_columns(
        pl.lit("Straight").alias("type"),
        (pl.lit("S") + pl.col("number").cast(pl.String)).alias("name"),
    )
    return pl.concat([corners, straights], how="diagonal_relaxed")


def first_datetime(car_df, pos_df):
    """Polars version of ``Session._get_first_datetime``: latest (Utc - timestamp) over car and position data."""
    starts = [
        utc_to_datetime(df.select("Utc", "timestamp"))
        .select((pl.col("Utc") - pl.col("timestamp").cast(pl.Duration("ns"))).max())
        .item()
        for df in (car_df, pos_df)
    ]
    return max(s for s in starts if s is not None)


def session_start_datetime(session_data_df):
    """Polars version of ``Session._get_session_start_datetime``: Utc of the first 'Started' status."""
    started = session_data_df.filter(pl.col("SessionStatus") == "Started").select("Utc")
    return utc_to_datetime(started).item(0, "Utc")
