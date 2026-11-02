"""Tests for the pandas / polars dataframe backend of a session's data lake."""
import sys
from datetime import datetime, timedelta

import pandas as pd
import pytest

from livef1.config import _settings, configure
from livef1.data_processing import backends
from livef1.data_processing.backends import check_backend_frame, configured_backend, validate_backend
from livef1.data_processing.data_models import BronzeTable
from livef1.models.session import Session

pl = pytest.importorskip("polars")

FRAME_TYPES = {"pandas": pd.DataFrame, "polars": pl.DataFrame}


@pytest.fixture(autouse=True)
def reset_backend_setting():
    previous = _settings.pop("dataframe_backend", None)
    yield
    _settings.pop("dataframe_backend", None)
    if previous is not None:
        _settings["dataframe_backend"] = previous


def test_default_backend_is_pandas():
    assert configured_backend() == "pandas"
    assert Session().dataframe_backend == "pandas"


def test_validate_backend_case():
    assert validate_backend("Polars") == "polars"


def test_configure_rejects_unknown_backend():
    with pytest.raises(ValueError, match="Unknown dataframe backend"):
        configure(dataframe_backend="spark")
    assert configured_backend() == "pandas"


def test_configure_polars_missing(monkeypatch):
    monkeypatch.setitem(sys.modules, "polars", None)
    with pytest.raises(ImportError, match=r"livef1\[polars\]"):
        configure(dataframe_backend="polars")


def test_configure_sets_backend():
    configure(dataframe_backend="polars")
    assert configured_backend() == "polars"
    assert Session().dataframe_backend == "polars"


def test_backend_is_configure_only():
    import inspect
    import livef1
    assert "engine" not in inspect.signature(livef1.get_session).parameters
    assert "dataframe_backend" not in inspect.signature(livef1.get_session).parameters
    with pytest.raises(AttributeError):
        Session().dataframe_backend = "polars"  # read-only


def test_get_silver_functions_per_backend():
    assert backends.get_silver_functions("pandas").__name__.endswith("silver_functions")
    assert backends.get_silver_functions("polars").__name__.endswith("silver_functions_polars")


def test_check_backend_frame():
    check_backend_frame(pl.DataFrame({"a": [1]}), "polars", "t")
    check_backend_frame(pd.DataFrame({"a": [1]}), "pandas", "t")
    check_backend_frame(None, "polars", "t")  # non-DataFrames are not checked
    with pytest.raises(TypeError, match="returned a pandas DataFrame"):
        check_backend_frame(pd.DataFrame({"a": [1]}), "polars", "t")
    with pytest.raises(TypeError, match="returned a polars DataFrame"):
        check_backend_frame(pl.DataFrame({"a": [1]}), "pandas", "t")


PARSED_CAR = [
    {"SessionKey": 9465, "timestamp": "00:00:49.985", "Utc": "2024-03-02T15:00:00.1234567Z", "DriverNo": "1",
     "rpm": 10000, "speed": 300, "n_gear": 7, "throttle": 100, "brake": 0},
    {"SessionKey": 9465, "timestamp": "01:02:03.004", "Utc": "2024-03-02T16:02:13.1Z", "DriverNo": "44",
     "rpm": 9000, "speed": 250, "n_gear": 6, "throttle": 80, "brake": 1},
]


def test_bronze_table_is_built_natively_per_backend():
    pandas_df = BronzeTable("CarData.z", {}, PARSED_CAR, dataframe_backend="pandas").df
    polars_df = BronzeTable("CarData.z", {}, PARSED_CAR, dataframe_backend="polars").df

    assert isinstance(pandas_df, pd.DataFrame)
    assert isinstance(polars_df, pl.DataFrame)
    assert polars_df.columns == list(pandas_df.columns)  # same renames (rpm -> RPM, ...)
    assert polars_df.schema["Speed"] == pl.Float32 and polars_df.schema["GearNo"] == pl.UInt8
    assert polars_df["timestamp"].to_list() == [timedelta(seconds=49.985), timedelta(hours=1, minutes=2, seconds=3.004)]
    assert polars_df["timestamp"].to_list() == list(pandas_df["timestamp"])



def test_bronze_timestamps_longer_than_a_day_match():
    stamps = ["00:00:01.234", "23:59:59.999", "1.00:00:00.500", "1.02:03:04.567", "12.10:00:00.000"]
    records = [{"timestamp": t, "A": 1} for t in stamps]
    pd_ts = BronzeTable("t", None, records).df["timestamp"]
    pl_ts = BronzeTable("t", None, records, dataframe_backend="polars").df["timestamp"]
    assert pd_ts.iloc[3] == pd.Timedelta(days=1, hours=2, minutes=3, seconds=4.567)
    assert list(pd_ts) == pl_ts.to_list()

def test_bronze_table_all_null_column_is_string():
    df = BronzeTable("RaceControlMessages", {}, [{"Message": "X", "Flag": None}], dataframe_backend="polars").df
    assert df.schema["Flag"] == pl.String


def test_backend_is_pinned_by_the_first_table():
    configure(dataframe_backend="polars")
    session = Session()
    other = Session()  # no tables yet: still follows configure()
    session.data_lake.create_bronze_table(table_name="CarData.z", raw_data={}, parsed_data=PARSED_CAR)

    configure(dataframe_backend="pandas")  # changing the setting later does not affect the pinned session
    assert session.dataframe_backend == "polars"
    assert isinstance(session.data_lake.get("bronze", "CarData.z").df, pl.DataFrame)
    session.data_lake.create_bronze_table(table_name="Position.z", raw_data={}, parsed_data=PARSED_CAR)
    assert isinstance(session.data_lake.get("bronze", "Position.z").df, pl.DataFrame)

    assert other.dataframe_backend == "pandas"


def test_polars_session_helpers_match_pandas():
    from livef1.data_processing import bronze_polars
    from livef1.utils import helper

    pos = [{**r, "X": 0, "Y": 0, "Z": 0} for r in PARSED_CAR]
    pd_car, pd_pos = (BronzeTable("t", {}, rows, dataframe_backend="pandas").df for rows in (PARSED_CAR, pos))
    pl_car, pl_pos = (BronzeTable("t", {}, rows, dataframe_backend="polars").df for rows in (PARSED_CAR, pos))
    expected = max(
        (helper.to_datetime(df["Utc"]) - pd.to_timedelta(df["timestamp"])).max() for df in (pd_car, pd_pos)
    )
    assert bronze_polars.first_datetime(pl_car, pl_pos) == expected.to_pydatetime()

    session_data = [{"Utc": "2024-03-02T15:00:00.5Z", "SessionStatus": "Inactive"},
                    {"Utc": "2024-03-02T15:01:02.0004999Z", "SessionStatus": "Started"}]
    assert bronze_polars.session_start_datetime(BronzeTable("t", {}, session_data, dataframe_backend="polars").df) == datetime(2024, 3, 2, 15, 1, 2)


def test_track_regions_match_pandas_circuit():
    from livef1.data_processing.bronze_polars import build_track_regions
    from livef1.models.circuit import Circuit

    raw = {"corners": [
        {"number": n, "angle": 10.0 * n, "length": length, "trackPosition": {"x": float(n), "y": -float(n)}}
        for n, length in [(1, 1000), (2, 1600), (3, 4000), (4, 9000)]
    ]}
    circuit = Circuit.__new__(Circuit)
    circuit.short_name = "Test"
    with pytest.MonkeyPatch.context() as mp:
        import copy
        mp.setattr("livef1.models.circuit.requests.get", lambda url, **kw: type("R", (), {
            "json": staticmethod(lambda: copy.deepcopy(raw) if "/circuits/" in url else {"1": {"name": "Test", "circuitKey": 1, "years": [2024]}}),
        })())
        try:
            circuit._load_circuit_data()
        except Exception:
            pytest.skip("Circuit loader needs a different mock for this version")

    expected = circuit.track_regions.reset_index(drop=True)
    got = build_track_regions(copy.deepcopy(raw)).to_pandas()
    for col in ["type", "name", "corner_start", "corner_end"]:
        assert got[col].tolist() == expected[col].tolist(), col


def _session_with_bronze(backend):
    configure(dataframe_backend=backend)
    session = Session()
    session.topic_names_info = {"Speeds": {"key": "Speeds", "default_is_stream": False}}
    session.data_lake.create_bronze_table(
        table_name="Speeds", raw_data={}, parsed_data=[{"DriverNo": "1", "Speed": 300.0}, {"DriverNo": "1", "Speed": 310.0}]
    )
    return session


@pytest.mark.parametrize("backend", ["pandas", "polars"])
def test_custom_table_gets_and_returns_backend_frames(backend):
    session = _session_with_bronze(backend)
    frame_type = FRAME_TYPES[backend]
    seen = {}

    @session.create_silver_table(table_name="MaxSpeed", source_tables=["Speeds"])
    def max_speed(Speeds):
        seen["type"] = type(Speeds)
        return frame_type({"MaxSpeed": [float(Speeds["Speed"].max())]})

    session.data_lake.get("silver", "MaxSpeed").generate_table()
    out = session.get_data("MaxSpeed", level="silver")
    assert seen["type"] is frame_type
    assert isinstance(out, frame_type)
    assert out["MaxSpeed"][0] == 310.0


@pytest.mark.parametrize("backend, wrong_type", [("pandas", pl.DataFrame), ("polars", pd.DataFrame)])
def test_custom_table_returning_other_backend_frame_raises(backend, wrong_type):
    session = _session_with_bronze(backend)

    @session.create_silver_table(table_name="Wrong", source_tables=["Speeds"])
    def wrong(Speeds):
        return wrong_type({"a": [1]})

    with pytest.raises(TypeError, match=f"uses the '{backend}' dataframe backend"):
        session.data_lake.get("silver", "Wrong").generate_table()


def test_race_control_messages_same_in_both_backends(mock_session):
    from livef1.data_processing import silver_functions, silver_functions_polars

    parsed = [
        {"SessionKey": 9465, "timestamp": f"01:3{i}:00.000", "Utc": "2024-03-02T15:30:00Z", "Category": cat,
         "Scope": scope, "Status": None, "Flag": flag, "Message": msg, "Lap": i + 1}
        for i, (cat, scope, flag, msg) in enumerate([
            ("Other", None, None, "TEST MESSAGE"),
            ("Flag", "Driver", "BLACK AND ORANGE", "BLACK AND ORANGE FLAG FOR CAR 1 (VER)"),
            ("Other", None, None, "CAR 1 (VER) NOTED - TRACK LIMITS"),
            ("Flag", "Driver", "BLUE", "WAVED BLUE FLAG FOR CAR 44 (HAM)"),
            ("Other", None, None, "5 SECOND TIME PENALTY FOR CAR 16 (LEC)"),
        ])
    ]
    cols = ["Category", "Scope", "Status", "info"]
    pandas_out = silver_functions.generate_race_control_messages_table(
        mock_session, BronzeTable("RaceControlMessages", {}, parsed, dataframe_backend="pandas").df)[cols]
    polars_out = silver_functions_polars.generate_race_control_messages_table(
        mock_session, BronzeTable("RaceControlMessages", {}, parsed, dataframe_backend="polars").df).select(cols)

    pandas_rows = [[None if pd.isna(v) else v for v in row] for row in pandas_out.astype(object).values.tolist()]
    assert pandas_rows == [list(row) for row in polars_out.rows()]
    assert pandas_rows[0][:2] == ["Other", "Unclassified"]
