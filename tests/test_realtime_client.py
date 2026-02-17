"""Tests for livef1.adapters.realtime_client.RealF1Client."""
import pytest
from unittest.mock import MagicMock, patch
from livef1.adapters.realtime_client import RealF1Client
from livef1.utils.exceptions import ArgumentError


def test_real_f1_client_init_topics_list():
    client = RealF1Client(topics=["CarData.z", "SessionInfo"], log_file_name=None)
    assert client.topics == ["CarData.z", "SessionInfo"]
    assert client._connection_url is not None
    assert client._handlers == {}


def test_real_f1_client_init_topics_string():
    client = RealF1Client(topics="DriverList", log_file_name=None)
    assert client.topics == ["DriverList"]


def test_real_f1_client_init_invalid_topics():
    with pytest.raises(ArgumentError, match="list of topics"):
        RealF1Client(topics=123, log_file_name=None)


def test_real_f1_client_callback_registration():
    client = RealF1Client(topics=["CarData.z"], log_file_name=None)

    @client.callback("process_telemetry")
    async def handler(records):
        pass

    assert "process_telemetry" in client._handlers
    assert callable(client._handlers["process_telemetry"])
