"""Tests for livef1.utils.exceptions."""
import pytest
from livef1.utils.exceptions import (
    livef1Exception,
    LiveF1Error,
    RealF1Error,
    ArgumentError,
    MissingFunctionError,
    TopicNotFoundError,
    AdapterError,
    InvalidResponseError,
    InvalidEndpointError,
    DataDecodingError,
    DataProcessingError,
    ParsingError,
    ETLError,
    SubscriptionError,
    DataFormatError,
)


def test_livef1_exception():
    with pytest.raises(livef1Exception) as exc_info:
        raise livef1Exception("test message")
    assert str(exc_info.value) == "test message"


def test_livef1_error_inheritance():
    assert issubclass(LiveF1Error, Exception)


def test_livef1_error_message():
    with pytest.raises(LiveF1Error) as exc_info:
        raise LiveF1Error("error message")
    assert "error message" in str(exc_info.value)


def test_real_f1_error_inheritance():
    with pytest.raises(RealF1Error):
        raise RealF1Error("realtime error")
    assert issubclass(RealF1Error, LiveF1Error)


def test_argument_error():
    with pytest.raises(ArgumentError) as exc_info:
        raise ArgumentError("missing argument")
    assert "missing argument" in str(exc_info.value)
    assert issubclass(ArgumentError, LiveF1Error)


def test_missing_function_error():
    with pytest.raises(MissingFunctionError) as exc_info:
        raise MissingFunctionError("no parser for X")
    assert "no parser" in str(exc_info.value)


def test_topic_not_found_error():
    with pytest.raises(TopicNotFoundError) as exc_info:
        raise TopicNotFoundError("Topic Foo not found")
    assert "Foo" in str(exc_info.value)


def test_adapter_error_inheritance():
    assert issubclass(AdapterError, LiveF1Error)


def test_invalid_response_error():
    with pytest.raises(InvalidResponseError) as exc_info:
        raise InvalidResponseError("invalid json")
    assert "invalid json" in str(exc_info.value)
    assert issubclass(InvalidResponseError, AdapterError)


def test_invalid_endpoint_error():
    with pytest.raises(InvalidEndpointError) as exc_info:
        raise InvalidEndpointError("404")
    assert "404" in str(exc_info.value)


def test_data_decoding_error():
    with pytest.raises(DataDecodingError):
        raise DataDecodingError("decode failed")


def test_data_processing_error_inheritance():
    assert issubclass(DataProcessingError, LiveF1Error)


def test_parsing_error():
    with pytest.raises(ParsingError) as exc_info:
        raise ParsingError("parse failed")
    assert "parse failed" in str(exc_info.value)
    assert issubclass(ParsingError, DataProcessingError)


def test_etl_error():
    with pytest.raises(ETLError) as exc_info:
        raise ETLError("ETL failed")
    assert "ETL failed" in str(exc_info.value)
    assert issubclass(ETLError, DataProcessingError)


def test_subscription_error():
    with pytest.raises(SubscriptionError):
        raise SubscriptionError("subscribe failed")
    assert issubclass(SubscriptionError, AdapterError)


def test_data_format_error():
    with pytest.raises(DataFormatError):
        raise DataFormatError("unexpected format")
    assert issubclass(DataFormatError, AdapterError)
