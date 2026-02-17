"""Tests for livef1.utils.helper."""
import base64
import json
import zlib
import pytest
import pandas as pd
import numpy as np
from livef1.utils.helper import (
    build_session_endpoint,
    json_parser_for_objects,
    parse,
    parse_hash,
    parse_helper_for_nested_dict,
    identifer_text_format,
    find_most_similar_vectorized,
    string_match_ratio,
    to_datetime,
)
from livef1.utils.constants import BASE_URL, STATIC_ENDPOINT
from livef1.utils.exceptions import LiveF1Error


def test_build_session_endpoint(session_path):
    result = build_session_endpoint(session_path)
    assert result.startswith(BASE_URL)
    assert STATIC_ENDPOINT in result
    assert session_path in result


def test_json_parser_for_objects():
    data = {"FooBar": 1, "BazQux": "two"}
    result = json_parser_for_objects(data)
    assert result == {"foobar": 1, "bazqux": "two"}


def test_json_parser_for_objects_empty():
    assert json_parser_for_objects({}) == {}


def test_parse_json_object():
    text = '{"a": 1, "b": 2}'
    result = parse(text)
    assert result == {"a": 1, "b": 2}


def test_parse_quoted_string():
    text = '"hello world"'
    result = parse(text)
    assert result == "hello world"


def test_parse_plain_text():
    result = parse("plain")
    assert result == "plain"


def test_parse_zipped():
    raw = b'{"x": 1}'
    compressor = zlib.compressobj(zlib.Z_DEFAULT_COMPRESSION, zlib.DEFLATED, -zlib.MAX_WBITS)
    compressed = compressor.compress(raw) + compressor.flush()
    b64 = base64.b64encode(compressed).decode("ascii")
    result = parse(b64, zipped=True)
    assert result == {"x": 1}


def test_parse_hash():
    raw = b'{"session": 9465}'
    compressor = zlib.compressobj(zlib.Z_DEFAULT_COMPRESSION, zlib.DEFLATED, -zlib.MAX_WBITS)
    compressed = compressor.compress(raw) + compressor.flush()
    b64 = base64.b64encode(compressed).decode("ascii")
    result = parse_hash(b64)
    assert result == {"session": 9465}


def test_parse_helper_for_nested_dict_flat():
    info = {"a": 1, "b": 2}
    record = {}
    result = parse_helper_for_nested_dict(info, record)
    assert result == {"a": 1, "b": 2}


def test_parse_helper_for_nested_dict_nested():
    info = {"outer": {"inner": 42}}
    record = {}
    result = parse_helper_for_nested_dict(info, record)
    assert result["outer_inner"] == 42


def test_parse_helper_for_nested_dict_list():
    info = {"sectors": [{"t": 1}, {"t": 2}]}
    record = {}
    result = parse_helper_for_nested_dict(info, record)
    assert "sectors_1_t" in result
    assert "sectors_2_t" in result
    assert result["sectors_1_t"] == 1
    assert result["sectors_2_t"] == 2


def test_identifer_text_format():
    result = identifer_text_format("Formula 1 Bahrain Grand Prix")
    assert "formula" not in result
    assert "1" not in result
    assert "grand" not in result
    assert "prix" not in result
    assert "bahrain" in result


def test_identifer_text_format_simple():
    result = identifer_text_format("Spa")
    assert result == ["spa"]


def test_find_most_similar_vectorized_jaccard():
    df = pd.DataFrame({
        "Meeting Offname": ["Bahrain Grand Prix", "Monaco Grand Prix"],
        "Meeting Name": ["Bahrain", "Monaco"],
    })
    result = find_most_similar_vectorized(df, "Bahrain")
    assert result["isFound"] == 1
    assert "bahrain" in result["value"].lower()
    assert result["how"] == "jaccard"


def test_find_most_similar_vectorized_not_found_raises():
    df = pd.DataFrame({
        "col": ["Alpha", "Beta", "Gamma"],
    })
    with pytest.raises(LiveF1Error):
        find_most_similar_vectorized(df, "XyZzYyNonsense")


def test_string_match_ratio_identical():
    assert string_match_ratio("abc", "abc") == 1.0


def test_string_match_ratio_half():
    assert string_match_ratio("ab", "ax") == 0.5


def test_string_match_ratio_empty():
    assert string_match_ratio("", "") == 0.0
    assert string_match_ratio("a", "") == 0.0


def test_string_match_ratio_different_lengths():
    assert string_match_ratio("abc", "ab") == 2 / 3


def test_to_datetime_series():
    s = pd.Series(["2024-03-02T15:00:00Z", "2024-03-02T16:00:00Z"])
    result = to_datetime(s)
    assert len(result) == 2
    assert hasattr(result, "year") or (hasattr(result, "__len__") and len(result) == 2)


def test_to_datetime_ndarray():
    arr = np.array(["2024-03-02T15:00:00Z"], dtype=object)
    result = to_datetime(arr)
    assert len(result) == 1
