"""Tests for livef1.adapters.realtime_client.RealF1Client and the SignalR Core client."""
import asyncio
import json
import time
import pytest
from unittest.mock import MagicMock, patch
from websockets.exceptions import ConnectionClosedOK

from livef1.adapters import signalrcore
from livef1.adapters.realtime_client import RealF1Client
from livef1.adapters.signalrcore import RECORD_SEPARATOR, SignalRCoreConnection, parse_frames
from livef1.auth import F1Token
from livef1.utils.exceptions import AdapterError, ArgumentError, AuthenticationError


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


def test_connection_url_is_signalrcore():
    client = RealF1Client(topics=["Heartbeat"])
    assert client._connection_url == "https://livetiming.formula1.com/signalrcore"


# --- SignalR Core client ---

def frames(*messages):
    return "".join(json.dumps(m) + RECORD_SEPARATOR for m in messages)


class FakeWebSocket:
    def __init__(self, incoming):
        self.incoming = list(incoming)
        self.sent = []
        self.closed = False

    async def send(self, message):
        self.sent.append(message)

    async def recv(self):
        if not self.incoming:
            raise ConnectionClosedOK(None, None)
        return self.incoming.pop(0)

    async def close(self):
        self.closed = True


def negotiate_response(status=200):
    resp = MagicMock()
    resp.status_code = status
    resp.json.return_value = {"connectionToken": "conn-token"}
    resp.cookies = {"AWSALBCORS": "sticky"}
    return resp


def test_parse_frames_splits_record_separator():
    text = frames({"type": 6}, {"type": 1, "target": "feed"})
    assert parse_frames(text) == [{"type": 6}, {"type": 1, "target": "feed"}]
    assert parse_frames(text.encode()) == parse_frames(text)


def test_connect_handshake_and_subscribe():
    ws = FakeWebSocket([frames({})])

    async def fake_connect(url, **kwargs):
        fake_connect.url, fake_connect.kwargs = url, kwargs
        return ws

    async def run():
        with patch.object(signalrcore.requests, "post", return_value=negotiate_response()) as post, \
                patch.object(signalrcore, "ws_connect", fake_connect):
            connection = await signalrcore.connect(
                "https://livetiming.formula1.com/signalrcore", {"Authorization": "Bearer abc"})
            await connection.invoke("Subscribe", [["Heartbeat"]])
            await connection.close()
        return post

    post = asyncio.run(run())
    assert post.call_args.args[0] == "https://livetiming.formula1.com/signalrcore/negotiate?negotiateVersion=1"
    assert fake_connect.url == "wss://livetiming.formula1.com/signalrcore?id=conn-token"
    assert fake_connect.kwargs["additional_headers"] == {"Authorization": "Bearer abc", "Cookie": "AWSALBCORS=sticky"}
    assert parse_frames(ws.sent[0]) == [{"protocol": "json", "version": 1}]
    assert parse_frames(ws.sent[1]) == [
        {"type": 1, "invocationId": "1", "target": "Subscribe", "arguments": [["Heartbeat"]]}
    ]
    assert ws.closed


def test_connect_handshake_error_closes_socket():
    ws = FakeWebSocket([frames({"error": "unsupported protocol"})])

    async def fake_connect(url, **kwargs):
        return ws

    async def run():
        with patch.object(signalrcore.requests, "post", return_value=negotiate_response()), \
                patch.object(signalrcore, "ws_connect", fake_connect):
            await signalrcore.connect("https://example.com/signalrcore", {})

    with pytest.raises(AdapterError, match="unsupported protocol"):
        asyncio.run(run())
    assert ws.closed


def test_connect_rejected_token():
    async def run():
        with patch.object(signalrcore.requests, "post", return_value=negotiate_response(status=401)):
            await signalrcore.connect("https://example.com/signalrcore", {})

    with pytest.raises(AuthenticationError):
        asyncio.run(run())


def test_messages_skip_pings_and_stop_on_close():
    ws = FakeWebSocket([
        frames({"type": 6}, {"type": 1, "target": "feed", "arguments": ["Heartbeat", {}, "t"]}),
        frames({"type": 7, "error": "server shutdown"}, {"type": 1, "target": "feed"}),
    ])

    async def run():
        connection = SignalRCoreConnection(ws, pending=[{"type": 3, "invocationId": "1", "result": {}}])
        received = [frame async for frame in connection.messages()]
        await connection.close()
        return received

    received = asyncio.run(run())
    assert [frame["type"] for frame in received] == [3, 1]


# --- dispatch and reconnect ---

def test_dispatch_snapshot_and_feed_reach_callbacks():
    client = RealF1Client(topics=["Heartbeat"])
    received = []

    @client.callback("collect")
    async def collect(records):
        received.append(records)

    async def run():
        await client._dispatch({"type": 3, "invocationId": "1",
                                "result": {"Heartbeat": {"Utc": "2026-10-23T22:25:00Z"}}})
        await client._dispatch({"type": 1, "target": "feed",
                                "arguments": ["Heartbeat", {"Utc": "2026-10-23T22:25:15Z"}, "2026-10-23T22:11:14Z"]})

    asyncio.run(run())
    assert [list(records) for records in received] == [["Heartbeat"], ["Heartbeat"]]
    assert received[0]["Heartbeat"][0]["timestamp"] is None
    assert received[1]["Heartbeat"][0]["timestamp"] == "2026-10-23T22:11:14Z"


def test_dispatch_handler_error_does_not_stop_stream():
    client = RealF1Client(topics=["Unknown"])

    @client.callback("collect")
    async def collect(records):
        pass

    asyncio.run(client._dispatch({"type": 1, "target": "feed", "arguments": ["NotATopic", {}, "t"]}))


class Stop(Exception):
    pass


class FakeConnection:
    def __init__(self):
        self.invoked = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc_info):
        return False

    async def invoke(self, target, arguments):
        self.invoked.append((target, arguments))

    async def messages(self):
        raise Stop()
        yield


def test_rejected_token_signs_in_again_once():
    client = RealF1Client(topics=["Heartbeat"])
    connection = FakeConnection()
    token = F1Token(value="abc", expires_at=time.time() + 3600)
    attempts = iter([AuthenticationError("rejected"), connection])

    async def fake_connect(url, headers):
        result = next(attempts)
        if isinstance(result, Exception):
            raise result
        return result

    with patch("livef1.adapters.realtime_client.login", return_value=token) as login, \
            patch("livef1.adapters.realtime_client.connect", fake_connect):
        with pytest.raises(Stop):
            asyncio.run(client._run())

    assert [call.kwargs["force"] for call in login.call_args_list] == [False, True]
    assert connection.invoked == [("Subscribe", [["Heartbeat"]])]
