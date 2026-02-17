"""Tests for livef1.data_processing.data_models and lakes."""
import pytest
import pandas as pd
from unittest.mock import MagicMock
from livef1.data_processing.data_models import (
    BasicResult,
    Table,
    BronzeTable,
    SilverTable,
    GoldTable,
)
from livef1.data_processing.lakes import (
    SimpleLake,
    BronzeLake,
    SilverLake,
    GoldLake,
    DataLake,
)


def test_basic_result():
    data = [{"rpm": 1000, "speed": 200, "n_gear": 4}]
    result = BasicResult(data)
    assert result.value == data
    assert hasattr(result, "df")
    assert isinstance(result.df, pd.DataFrame)
    assert "RPM" in result.df.columns or "Speed" in result.df.columns


def test_basic_result_str():
    data = [{"rpm": 1000}]
    result = BasicResult(data)
    assert isinstance(str(result), str)


def test_table_init():
    t = Table("test_table", data_lake=None)
    assert t.table_name == "test_table"
    assert t.table is None
    assert t.callback is None
    assert t.df is None


def test_table_generate_table_with_callback():
    lake = MagicMock()
    t = Table("t1", data_lake=lake)
    t.callback = lambda self: pd.DataFrame({"a": [1]})
    out = t.generate_table()
    assert out is not None
    assert isinstance(out, pd.DataFrame)
    assert lake.update_metadata.called


def test_bronze_table():
    raw = {"k": "v"}
    parsed = [{"rpm": 1000, "speed": 200}]
    t = BronzeTable("bronze1", data=raw, parsed_data=parsed, data_lake=None)
    assert t.table_name == "bronze1"
    assert t.raw == raw
    assert isinstance(t.df, pd.DataFrame)
    assert len(t.df) == 1


def test_silver_table_init():
    t = SilverTable("silver1", sources=["laps"], data_lake=None)
    assert t.table_name == "silver1"
    assert t.sources == ["laps"]
    assert set(t.source_tables.keys()) == {"bronze", "silver", "gold"}
    assert t.source_tables["bronze"] == []
    assert t.source_tables["silver"] == []
    assert t.source_tables["gold"] == []
    assert t.df is None


def test_gold_table_init():
    t = GoldTable("gold1", sources=["SectorDiff"], data_lake=None)
    assert t.table_name == "gold1"
    assert t.sources == ["SectorDiff"]


def test_simple_lake_put_has_data_get():
    great_lake = MagicMock()
    lake = SimpleLake(great_lake)
    table = Table("t1", data_lake=great_lake)
    lake.put("t1", table)
    assert lake.has_data("t1")
    got = lake.get("t1")
    assert got is table


def test_simple_lake_get_missing():
    great_lake = MagicMock()
    lake = SimpleLake(great_lake)
    assert lake.get("nonexistent") is None


def test_bronze_lake_type():
    great_lake = MagicMock()
    lake = BronzeLake(great_lake)
    assert lake.lake_type == "bronze"


def test_silver_lake_type():
    great_lake = MagicMock()
    lake = SilverLake(great_lake)
    assert lake.lake_type == "silver"


def test_gold_lake_type():
    great_lake = MagicMock()
    lake = GoldLake(great_lake)
    assert lake.lake_type == "gold"


def test_data_lake_init():
    session = MagicMock()
    dl = DataLake(session)
    assert dl.session is session
    assert dl.metadata == {}
    assert dl.bronze is not None
    assert dl.silver is not None
    assert dl.gold is not None


def test_data_lake_update_metadata():
    session = MagicMock()
    dl = DataLake(session)
    dl.update_metadata("t1", "bronze", generated=False)
    assert "t1" in dl.metadata
    assert dl.metadata["t1"]["table_type"] == "bronze"
    assert dl.metadata["t1"]["generated"] is False


def test_data_lake_put_get_bronze():
    session = MagicMock()
    dl = DataLake(session)
    table = BronzeTable("b1", data={}, parsed_data=[{"rpm": 1}], data_lake=dl)
    dl.put("bronze", "b1", table)
    got = dl.get("bronze", "b1")
    assert got is table


def test_data_lake_put_invalid_level():
    session = MagicMock()
    dl = DataLake(session)
    with pytest.raises(ValueError, match="Invalid level"):
        dl.put("invalid", "t1", MagicMock())


def test_data_lake_get_invalid_level():
    session = MagicMock()
    dl = DataLake(session)
    with pytest.raises(ValueError, match="Invalid level"):
        dl.get("invalid", "t1")


def test_data_lake_create_bronze_table():
    session = MagicMock()
    dl = DataLake(session)
    dl.create_bronze_table("b1", raw_data={"k": "v"}, parsed_data=[{"rpm": 100}])
    assert "b1" in dl.metadata
    got = dl.get("bronze", "b1")
    assert got is not None
    assert got.table_name == "b1"


def test_data_lake__identify_table_level_from_metadata():
    session = MagicMock()
    dl = DataLake(session)
    dl.metadata["t1"] = {"table_type": "silver", "created_at": None, "generated": False}
    assert dl._identify_table_level("t1") == "silver"


def test_data_lake__check_circular_dependencies_no_tables():
    session = MagicMock()
    dl = DataLake(session)
    assert dl._check_circular_dependencies() is True


def test_data_lake__check_circular_dependencies_silver_no_deps():
    session = MagicMock()
    dl = DataLake(session)
    silver = SilverTable("s1", sources=["TimingData"], data_lake=dl)
    silver.dependency_tables = []
    dl.put("silver", "s1", silver)
    dl.metadata["s1"] = {"table_type": "silver", "created_at": None, "generated": False}
    assert dl._check_circular_dependencies() is True
