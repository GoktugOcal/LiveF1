"""Minimal ASP.NET Core SignalR client (JSON protocol over WebSockets).

Covers what the live timing hub needs: negotiate, handshake, invoking hub
methods, receiving invocations and completions, and keep-alive pings.
"""

import asyncio
import json
from urllib.parse import urlencode

import requests
from websockets.asyncio.client import connect as ws_connect
from websockets.exceptions import ConnectionClosedOK, InvalidStatus

from ..utils.exceptions import AdapterError, AuthenticationError
from ..utils.logger import logger

__all__ = ["SignalRCoreConnection", "connect", "parse_frames"]

RECORD_SEPARATOR = "\x1e"
NEGOTIATE_TIMEOUT = (5, 30)
HANDSHAKE_TIMEOUT = 10
# the server drops clients that are silent for 30 seconds
PING_INTERVAL = 15

INVOCATION = 1
COMPLETION = 3
PING = 6
CLOSE = 7


def parse_frames(text) -> list:
    """Split a websocket message into its JSON frames."""
    if isinstance(text, bytes):
        text = text.decode("utf-8")
    return [json.loads(part) for part in text.split(RECORD_SEPARATOR) if part]


class SignalRCoreConnection:
    """An open hub connection. Use :func:`connect` to create one."""

    def __init__(self, ws, pending=None):
        self._ws = ws
        self._pending = list(pending or [])
        self._invocation_id = 0
        self._ping_task = asyncio.create_task(self._ping())

    async def invoke(self, target: str, arguments: list) -> str:
        """Call a hub method and return its invocation id; the result arrives as a completion frame."""
        self._invocation_id += 1
        invocation_id = str(self._invocation_id)
        await self._send({
            "type": INVOCATION,
            "invocationId": invocation_id,
            "target": target,
            "arguments": arguments,
        })
        return invocation_id

    async def messages(self):
        """Yield invocation and completion frames until the connection closes."""
        while True:
            if self._pending:
                frames, self._pending = self._pending, []
            else:
                try:
                    frames = parse_frames(await self._ws.recv())
                except ConnectionClosedOK:
                    return
                except json.JSONDecodeError as exc:
                    logger.warning(f"Skipping a malformed live timing message: {exc}")
                    continue
            for frame in frames:
                kind = frame.get("type")
                if kind == CLOSE:
                    if frame.get("error"):
                        logger.warning(f"Live timing closed the connection: {frame['error']}")
                    return
                if kind in (INVOCATION, COMPLETION):
                    yield frame

    async def close(self):
        self._ping_task.cancel()
        await self._ws.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc_info):
        await self.close()

    async def _send(self, message: dict):
        await self._ws.send(json.dumps(message) + RECORD_SEPARATOR)

    async def _ping(self):
        while True:
            await asyncio.sleep(PING_INTERVAL)
            await self._send({"type": PING})


async def connect(base_url: str, headers: dict) -> SignalRCoreConnection:
    """
    Negotiate with the hub at ``base_url`` and open a WebSocket connection.

    Parameters
    ----------
    base_url : str
        Hub URL, e.g. ``https://livetiming.formula1.com/signalrcore``.
    headers : dict
        HTTP headers sent with the negotiate request and the WebSocket handshake.

    Raises
    ------
    AuthenticationError
        If the server rejects the credentials.
    AdapterError
        If the negotiate response or the SignalR handshake is invalid.
    """
    base_url = base_url.rstrip("/")
    resp = await asyncio.to_thread(
        requests.post,
        f"{base_url}/negotiate?negotiateVersion=1",
        headers=headers,
        timeout=NEGOTIATE_TIMEOUT,
    )
    if resp.status_code in (401, 403):
        raise AuthenticationError(f"Live timing rejected the connection (HTTP {resp.status_code}).")
    resp.raise_for_status()
    try:
        connection_token = resp.json()["connectionToken"]
    except (ValueError, KeyError, TypeError):
        raise AdapterError("Unexpected negotiate response from live timing.") from None

    ws_headers = dict(headers)
    # the load balancer cookie keeps the socket on the server that negotiated it
    if resp.cookies:
        ws_headers["Cookie"] = "; ".join(f"{name}={value}" for name, value in resp.cookies.items())
    ws_url = base_url.replace("https://", "wss://", 1).replace("http://", "ws://", 1)
    ws_url = f"{ws_url}?{urlencode({'id': connection_token})}"

    try:
        ws = await ws_connect(ws_url, additional_headers=ws_headers, user_agent_header=None, max_size=None)
    except InvalidStatus as exc:
        status = exc.response.status_code
        if status in (401, 403):
            raise AuthenticationError(f"Live timing rejected the connection (HTTP {status}).") from None
        raise

    try:
        await ws.send(json.dumps({"protocol": "json", "version": 1}) + RECORD_SEPARATOR)
        frames = parse_frames(await asyncio.wait_for(ws.recv(), HANDSHAKE_TIMEOUT))
        if not frames or frames[0].get("error"):
            error = frames[0].get("error") if frames else "empty response"
            raise AdapterError(f"SignalR handshake failed: {error}")
    except BaseException:
        await ws.close()
        raise
    return SignalRCoreConnection(ws, pending=frames[1:])
