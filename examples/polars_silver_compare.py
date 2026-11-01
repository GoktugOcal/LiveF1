"""
Generate the silver tables with the pandas and the polars dataframe backend and compare them.

    python examples/polars_silver_compare.py 2026 British Race [--no-peak]

Each backend gets its own session, built after livef1.configure(dataframe_backend="pandas" / "polars").

Reports value differences per table, per-table generation time, output table
size, and peak memory used while generating (each pipeline in a fresh process;
skip with --no-peak).
"""
import functools
import sys
import threading
import time
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import get_context

import numpy as np
import pandas as pd
import polars as pl
import psutil

import livef1
from livef1.data_processing.data_models import BronzeTable, SilverTable
from livef1.utils.constants import SILVER_SESSION_TABLES

BACKENDS = ["pandas", "polars"]

BRONZE_TOPICS = [
    "CarData.z", "Position.z", "SessionStatus", "Session_Data", "TimingData",
    "RaceControlMessages", "TyreStintSeries", "TrackStatus", "PitStopSeries",
]

SORT_KEYS = {
    "laps": ["DriverNo", "LapNo"],
    "carTelemetry": ["DriverNo", "Utc"],
    "raceControlMessages": ["timestamp", "Message"],
}


def _to_text(v):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return None
    if isinstance(v, (list, tuple, np.ndarray)):
        return str([int(x) for x in v])
    return str(v)


def _normalize(df, keys):
    df = df.drop(columns=["Driver"], errors="ignore").copy()
    for c in df.columns:
        s = df[c]
        if isinstance(s.dtype, pd.CategoricalDtype):
            s = df[c] = s.astype(s.cat.categories.dtype)
        if pd.api.types.is_timedelta64_dtype(s):
            df[c] = s.astype("timedelta64[ns]")
        elif pd.api.types.is_datetime64_any_dtype(s):
            df[c] = s.astype("datetime64[ns]")
        elif pd.api.types.is_numeric_dtype(s) and not pd.api.types.is_bool_dtype(s):
            df[c] = s.astype("float64")
        else:
            df[c] = s.map(_to_text).astype(object)
    return df.sort_values(keys, kind="stable").reset_index(drop=True)


def compare(name, pdf, pldf):
    keys = SORT_KEYS[name]
    a = _normalize(pdf, keys)
    b = _normalize(pldf.drop("Driver", strict=False).to_pandas(), keys)
    print(f"\n=== {name}: pandas {a.shape} | polars {b.shape}")
    n_dup = int(a.duplicated().sum())
    if n_dup and len(a) - n_dup == len(b):
        # pandas exact-timestamp outer joins duplicate rows when the right side has repeated keys
        print(f"  pandas has {n_dup} fully duplicated rows (join artifacts), dropped before comparing")
        a = a.drop_duplicates().reset_index(drop=True)
    missing = [c for c in a.columns if c not in b.columns]
    if missing:
        print("  columns missing in polars:", missing)
    if len(a) != len(b):
        print("  ROW COUNT MISMATCH")
        return False
    ok = True
    for c in a.columns:
        if c not in b.columns:
            continue
        x, y = a[c], b[c]
        if pd.api.types.is_float_dtype(x):
            eq = np.isclose(x.to_numpy(), y.astype("float64").to_numpy(), rtol=1e-4, atol=1e-3, equal_nan=True)
        else:
            eq = ((x == y) | (x.isna() & y.isna())).to_numpy()
        n_bad = int((~eq).sum())
        if n_bad:
            ok = False
            idx = np.flatnonzero(~eq)[:3]
            print(f"  {c}: {n_bad} mismatches, e.g. rows {idx.tolist()}: pandas={x.iloc[idx].tolist()} polars={y.iloc[idx].tolist()}")
    print("  OK" if ok else "  DIFFERENCES FOUND")
    return ok


def preload_bronze(session):
    """Load every bronze topic the silver tables need, so timings exclude downloading/parsing."""
    for topic in BRONZE_TOPICS:
        try:
            session.get_data(topic)
        except Exception:
            pass


def time_tables(durations):
    """
    Patch table building to record durations into `durations[backend]`: per silver table,
    plus the total time spent building bronze DataFrames from the parsed records.
    """
    original_bronze_init = BronzeTable.__init__

    def timed_bronze_init(self, *args, dataframe_backend="pandas", **kwargs):
        t0 = time.perf_counter()
        original_bronze_init(self, *args, dataframe_backend=dataframe_backend, **kwargs)
        durations[f"{dataframe_backend}_bronze"] = durations.get(f"{dataframe_backend}_bronze", 0.0) + time.perf_counter() - t0
    BronzeTable.__init__ = timed_bronze_init

    original = SilverTable.generate_table

    def timed_generate_table(self):
        t0 = time.perf_counter()
        out = original(self)
        durations[self.data_lake.session.dataframe_backend][self.table_name] = time.perf_counter() - t0
        return out
    SilverTable.generate_table = timed_generate_table


def table_memory_mb(df):
    """In-memory size of a silver table, without the `Driver` object column (not comparable across libraries)."""
    if isinstance(df, pl.DataFrame):
        return df.drop("Driver", strict=False).estimated_size() / 2**20
    return df.drop(columns=["Driver"], errors="ignore").memory_usage(deep=True).sum() / 2**20


def bronze_memory_mb(session):
    return sum(table_memory_mb(table.df) for table in session.data_lake.bronze.lake.values() if table.df is not None)


def run_pipeline(session):
    session.generate(silver=True)
    return {name: session.get_data(name, level="silver") for name in SILVER_SESSION_TABLES}


def measure_peak_memory(backend, season, meeting, session_name):
    """
    Run one pipeline in a fresh process and return the peak extra RSS (MB) it needs on
    top of the already-loaded bronze data. RSS is sampled from a background thread.
    """
    livef1.configure(dataframe_backend=backend)
    session = livef1.get_session(season, meeting, session_name)
    preload_bronze(session)

    process = psutil.Process()
    baseline = peak = process.memory_info().rss
    done = threading.Event()

    def sample():
        nonlocal peak
        while not done.is_set():
            peak = max(peak, process.memory_info().rss)
            time.sleep(0.005)

    sampler = threading.Thread(target=sample, daemon=True)
    sampler.start()
    run_pipeline(session)
    done.set()
    sampler.join()
    peak = max(peak, process.memory_info().rss)
    return (peak - baseline) / 2**20


def print_performance(durations, sizes, peaks, bronze_sizes):
    names = SILVER_SESSION_TABLES
    print("\n=== Performance (silver rows: bronze already loaded)")
    print(f"  {'table':<22}{'pandas time':>12}{'polars time':>12}{'speedup':>9}{'pandas MB':>11}{'polars MB':>11}")
    for name in names:
        t_pd, t_pl = durations["pandas"].get(name, np.nan), durations["polars"].get(name, np.nan)
        m_pd, m_pl = sizes["pandas"].get(name, np.nan), sizes["polars"].get(name, np.nan)
        print(f"  {name:<22}{t_pd:>11.2f}s{t_pl:>11.2f}s{t_pd / t_pl:>8.1f}x{m_pd:>11.1f}{m_pl:>11.1f}")
    tot_pd, tot_pl = sum(durations["pandas"].values()), sum(durations["polars"].values())
    print(f"  {'total (tables)':<22}{tot_pd:>11.2f}s{tot_pl:>11.2f}s{tot_pd / tot_pl:>8.1f}x"
          f"{sum(sizes['pandas'].values()):>11.1f}{sum(sizes['polars'].values()):>11.1f}")
    print(f"  {'bronze build':<22}{durations['pandas_bronze']:>11.2f}s{durations['polars_bronze']:>11.2f}s"
          f"{durations['pandas_bronze'] / durations['polars_bronze']:>8.1f}x{bronze_sizes['pandas']:>11.1f}{bronze_sizes['polars']:>11.1f}")
    print(f"  {'total (generate call)':<22}{durations['pandas_total']:>11.2f}s{durations['polars_total']:>11.2f}s"
          f"{durations['pandas_total'] / durations['polars_total']:>8.1f}x")
    if peaks:
        print(f"  {'peak extra RSS':<22}{peaks['pandas']:>10.0f}MB{peaks['polars']:>10.0f}MB")
    print("  (bronze build = DataFrames built from the parsed records, MB = size of all bronze tables;")
    print("   table MB = size of the output tables; peak extra RSS = memory used while generating, measured in a fresh process)")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    season, meeting, session_name = (int(args[0]), args[1], args[2]) if len(args) > 2 else (2026, "British", "Race")

    durations = {backend: {} for backend in BACKENDS}
    time_tables(durations)

    tables, bronze_sizes = {}, {}
    for backend in BACKENDS:
        # The session takes the configured backend when it loads its first (bronze) table
        livef1.configure(dataframe_backend=backend)
        session = livef1.get_session(season, meeting, session_name)
        preload_bronze(session)
        t0 = time.perf_counter()
        tables[backend] = run_pipeline(session)
        durations[f"{backend}_total"] = time.perf_counter() - t0
        bronze_sizes[backend] = bronze_memory_mb(session)
    sizes = {backend: {name: table_memory_mb(df) for name, df in tables[backend].items()} for backend in BACKENDS}

    peaks = {}
    if "--no-peak" not in sys.argv:
        for backend in BACKENDS:
            # One pool per backend so each measurement gets its own fresh process
            with ProcessPoolExecutor(max_workers=1, mp_context=get_context("spawn")) as pool:
                peaks[backend] = pool.submit(measure_peak_memory, backend, season, meeting, session_name).result()

    results = {}
    for name in SILVER_SESSION_TABLES:
        assert isinstance(tables["polars"][name], pl.DataFrame) and isinstance(tables["pandas"][name], pd.DataFrame)
        results[name] = compare(name, tables["pandas"][name], tables["polars"][name])

    print_performance(durations, sizes, peaks, bronze_sizes)
    print("\nSUMMARY:", results)
