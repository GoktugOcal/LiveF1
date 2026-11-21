"""Small helpers shared by the analysis functions (pandas only)."""
import re

import numpy as np
import pandas as pd


def to_timedelta(values):
    """
    Convert lap or sector times to ``timedelta64[ns]``.

    Accepts timedeltas, numbers (seconds) and strings such as ``"1:32.456"`` or
    ``"32.456"``. Anything that cannot be parsed becomes ``NaT``.
    """
    s = pd.Series(values) if not isinstance(values, pd.Series) else values
    if pd.api.types.is_timedelta64_dtype(s):
        return s.astype("timedelta64[ns]")
    if pd.api.types.is_numeric_dtype(s):
        return pd.to_timedelta(s.astype(float), unit="s")

    def parse(value):
        if value is None or (isinstance(value, float) and np.isnan(value)):
            return pd.NaT
        if isinstance(value, pd.Timedelta):
            return value
        if isinstance(value, (int, float, np.integer, np.floating)):
            return pd.Timedelta(seconds=float(value))
        text = str(value).strip()
        if not text:
            return pd.NaT
        # "M:SS.fff" or "H:MM:SS.fff" -> pad to "HH:MM:SS.fff" for pandas
        if re.fullmatch(r"\d+:\d{1,2}(\.\d+)?", text):
            text = "00:" + text
        elif re.fullmatch(r"\d+(\.\d+)?", text):
            return pd.Timedelta(seconds=float(text))
        try:
            return pd.Timedelta(text)
        except (ValueError, TypeError):
            return pd.NaT

    return s.map(parse).astype("timedelta64[ns]")


def to_seconds(values):
    """Lap or sector times as float seconds."""
    return to_timedelta(values).dt.total_seconds()


def driver_key(values):
    """Driver numbers as strings (categoricals and ints compare equal to the string form)."""
    s = pd.Series(values) if not isinstance(values, pd.Series) else values
    s = s.astype(object)
    missing = s.isna().to_numpy()
    out = s.astype(str).astype(object)
    out[missing] = None
    return out


def status_codes(value):
    """Split a track status string such as ``"1,2"`` into a set of codes."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return set()
    return {code.strip() for code in str(value).split(",") if code.strip() and code.strip() != "nan"}


def empty_frame(columns):
    """A DataFrame with the given columns and no rows."""
    return pd.DataFrame({col: pd.Series(dtype=object) for col in columns})


def add_driver_info(df, driver_info, columns=("Tla", "FullName", "TeamName", "TeamColour")):
    """Join display fields from the ``driverInfo`` table onto ``df`` by ``DriverNo``."""
    if driver_info is None or len(driver_info) == 0 or "DriverNo" not in df.columns:
        for col in columns:
            if col not in df.columns:
                df[col] = None
        return df
    info = driver_info[["DriverNo", *[c for c in columns if c in driver_info.columns]]].copy()
    info["DriverNo"] = driver_key(info["DriverNo"])
    info = info.drop_duplicates("DriverNo")
    out = df.copy()
    out["DriverNo"] = driver_key(out["DriverNo"])
    out = out.drop(columns=[c for c in columns if c in out.columns]).merge(info, on="DriverNo", how="left")
    for col in columns:
        if col not in out.columns:
            out[col] = None
    return out
