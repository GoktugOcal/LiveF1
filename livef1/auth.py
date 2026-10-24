"""F1 account sign-in for livetiming.formula1.com.

Live timing data requires an F1TV subscription. :func:`login` signs in to the
Formula 1 account with a username and password and keeps the resulting
subscription token, which is then sent as a Bearer token with every request
to livetiming.formula1.com.

Credentials are read from ``F1_USERNAME`` and ``F1_PASSWORD``, either from
the environment or from a ``.env`` file. When they are missing, the user is
prompted and the entered values are saved to the ``.env`` file. The ``.env``
file is the first one found in the working directory or one of its parents.

The token is saved to ``~/.livef1/f1tv_auth_token.json``, or to ``LIVEF1_TOKEN_PATH``
if set, and reused until it expires.
"""

import base64
import getpass
import hashlib
import json
import os
import re
import secrets
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

import requests

from .config import _settings
from .utils.exceptions import AuthenticationError
from .utils.logger import logger

__all__ = ["F1Token", "login", "logout", "auth_header"]

ACCOUNT_ORIGIN = "https://account.formula1.com"
IDP_ORIGIN = "https://id.formula1.com"
CONFIG_SCRIPT_URL = f"{ACCOUNT_ORIGIN}/scripts/main.min.js"
AUTHORIZE_URL = f"{IDP_ORIGIN}/as/authorize"
TOKEN_URL = f"{IDP_ORIGIN}/as/token"

TIMEOUT = (5, 30)
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/141.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}
# makes the PingOne flow answer with JSON instead of HTML pages
PING_SDK_HEADERS = {"X-Requested-With": "ping-sdk"}

ENV_USERNAME = "F1_USERNAME"
ENV_PASSWORD = "F1_PASSWORD"
ENV_CLIENT_ID = "LIVEF1_F1_CLIENT_ID"
ENV_POLICY_ID = "LIVEF1_F1_POLICY_ID"
ENV_TOKEN_PATH = "LIVEF1_TOKEN_PATH"

DEFAULT_TOKEN_PATH = Path.home() / ".livef1" / "f1tv_auth_token.json"
ENV_FILE_NAME = ".env"

# a token expiring within this many seconds is treated as expired
EXPIRY_MARGIN = 300

_token = None


@dataclass(frozen=True)
class F1Token:
    """F1TV subscription token sent as Bearer token to livetiming.

    Attributes
    ----------
    value : str
        The subscription JWT.
    expires_at : float
        Unix timestamp of the token expiry.
    """
    value: str = field(repr=False)
    expires_at: float

    @property
    def expired(self) -> bool:
        return time.time() >= self.expires_at - EXPIRY_MARGIN

    @property
    def header(self) -> dict:
        return {"Authorization": f"Bearer {self.value}"}

    @classmethod
    def from_access_token(cls, access_token: str) -> "F1Token":
        """Create the token from the ``subscriptionToken`` claim of an OAuth access token."""
        subscription = _jwt_claims(access_token).get("subscriptionToken")
        if not isinstance(subscription, str) or not subscription:
            raise AuthenticationError(
                "The F1 account has no subscription token. "
                "An active F1TV subscription is required."
            )
        try:
            expires_at = float(_jwt_claims(subscription)["exp"])
        except (KeyError, TypeError, ValueError):
            raise AuthenticationError("The subscription token has no valid expiry.") from None
        return cls(value=subscription, expires_at=expires_at)


def login(
    username: str = None,
    password: str = None,
    *,
    force: bool = False,
    save_token: bool = None,
    token_path=None,
    env_path=None,
) -> F1Token:
    """
    Sign in to the F1 account and return the live timing token.

    A saved token that has not expired is reused without signing in, unless
    ``force`` is True.

    Parameters
    ----------
    username, password : str, optional
        F1 account credentials. If omitted, ``F1_USERNAME`` and ``F1_PASSWORD``
        are read from the environment or from ``env_path``. If they are still
        missing, the user is prompted and the entered values are saved to
        ``env_path`` after a successful sign-in.
    force : bool, optional
        Sign in again even if a valid token exists. Default is False.
    save_token : bool, optional
        Save the token to ``token_path``. If False, the token is kept in
        memory only. Default is True.
    token_path : str or pathlib.Path, optional
        Where the token is saved. If given, the absolute path is also saved
        as ``LIVEF1_TOKEN_PATH`` in ``env_path``, so later runs find the
        token without passing it again. Default is ``LIVEF1_TOKEN_PATH``
        from the environment or ``env_path``, else ``~/.livef1/f1tv_auth_token.json``.
    env_path : str or pathlib.Path, optional
        The ``.env`` file credentials are read from and saved to. Default is
        the first ``.env`` in the current working directory or one of its
        parents, else ``.env`` in the current working directory.

    Defaults of ``save_token``, ``token_path`` and ``env_path`` can be set
    with :func:`livef1.configure`.

    Returns
    -------
    F1Token
        The live timing token.

    Raises
    ------
    AuthenticationError
        If no credentials are available or the sign-in fails.

    Examples
    --------
    >>> import livef1
    >>> livef1.login()  # .env, environment or prompt
    >>> livef1.login(force=True, save_token=False)
    """
    global _token
    save_token = _setting("auth_save_token", save_token, True)
    env_path = _env_path(env_path)
    remember = {}
    if token_path is not None and save_token:
        explicit = Path(token_path).expanduser().resolve()
        if _token_path(None, env_path).resolve() != explicit:
            remember[ENV_TOKEN_PATH] = str(explicit)
    token_path = _token_path(token_path, env_path)

    if not force and (token := _valid_token(token_path)):
        logger.debug("Using the saved F1 account token.")
        _save_env(env_path, remember)
        return token

    username, password, prompted = _credentials(username, password, env_path)
    logger.info("Signing in to the F1 account...")
    token = F1Token.from_access_token(_sign_in(username, password))
    _token = token
    logger.info("Signed in to the F1 account.")

    if save_token:
        try:
            _write_private(token_path, json.dumps({"token": token.value, "expires_at": token.expires_at}))
        except OSError as exc:
            logger.warning(f"Could not save the F1 account token to {token_path}: {exc}")
    _save_env(env_path, {**prompted, **remember})
    return token


def logout(token_path=None):
    """
    Forget the live timing token, in memory and on disk.

    The credentials in the ``.env`` file are kept.

    Parameters
    ----------
    token_path : str or pathlib.Path, optional
        The saved token to delete. Default is the configured token path.
    """
    global _token
    _token = None
    try:
        _token_path(token_path).unlink()
    except FileNotFoundError:
        pass


def auth_header() -> dict:
    """Return the ``Authorization`` header of a valid token, or ``{}`` if there is none."""
    try:
        token = _valid_token(_token_path(None))
    except Exception:
        return {}
    return token.header if token else {}


def _setting(name, value, default):
    if value is not None:
        return value
    configured = _settings.get(name)
    return default if configured is None else configured


def _env_path(env_path) -> Path:
    configured = _setting("auth_env_path", env_path, None)
    if configured is not None:
        return Path(configured).expanduser()
    cwd = Path.cwd()
    for directory in (cwd, *cwd.parents):
        if (candidate := directory / ENV_FILE_NAME).is_file():
            return candidate
    return cwd / ENV_FILE_NAME


def _token_path(token_path, env_path=None) -> Path:
    path = (
        _setting("auth_token_path", token_path, None)
        or os.environ.get(ENV_TOKEN_PATH)
        or _read_env(env_path or _env_path(None)).get(ENV_TOKEN_PATH)
        or DEFAULT_TOKEN_PATH
    )
    return Path(path).expanduser()


def _save_env(env_path: Path, updates: dict):
    """Save ``updates`` to the ``.env`` file, logging only the keys."""
    if not updates:
        return
    try:
        _write_env(env_path, updates)
        logger.info(f"Saved {', '.join(updates)} to {env_path}.")
    except OSError as exc:
        logger.warning(f"Could not save {', '.join(updates)} to {env_path}: {exc}")


def _valid_token(token_path: Path):
    global _token
    if _token is not None and not _token.expired:
        return _token
    try:
        data = json.loads(token_path.read_text())
        stored = F1Token(value=data["token"], expires_at=float(data["expires_at"]))
    except (OSError, ValueError, KeyError, TypeError):
        return None
    if stored.expired:
        return None
    _token = stored
    return stored


def _jwt_claims(token: str) -> dict:
    # only reads the claims; livetiming verifies the signature
    try:
        payload = token.split(".")[1]
        claims = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
    except (AttributeError, IndexError, ValueError):
        raise AuthenticationError("Could not decode the F1 account token.") from None
    if not isinstance(claims, dict):
        raise AuthenticationError("Could not decode the F1 account token.")
    return claims


def _credentials(username, password, env_path: Path):
    """Return ``(username, password, prompted)``; ``prompted`` holds the values entered by the user."""
    from_file = _read_env(env_path)
    username = username or os.environ.get(ENV_USERNAME) or from_file.get(ENV_USERNAME)
    password = password or os.environ.get(ENV_PASSWORD) or from_file.get(ENV_PASSWORD)
    prompted = {}
    if username and password:
        return username, password, prompted

    missing = (
        f"No F1 account credentials found. Set {ENV_USERNAME} and {ENV_PASSWORD} "
        f"in the environment or in {env_path}, or call livef1.login(username, password)."
    )
    if not _can_prompt():
        raise AuthenticationError(missing)
    try:
        if not username:
            username = prompted[ENV_USERNAME] = input("F1 account email: ").strip()
        if not password:
            password = prompted[ENV_PASSWORD] = getpass.getpass("F1 account password: ")
    except EOFError:
        raise AuthenticationError(missing) from None
    if not (username and password):
        raise AuthenticationError(missing)
    return username, password, prompted


def _can_prompt() -> bool:
    return bool(sys.stdin and sys.stdin.isatty()) or "ipykernel" in sys.modules


def _read_env(path: Path) -> dict:
    """Parse ``KEY=value`` lines of a ``.env`` file."""
    try:
        lines = Path(path).read_text().splitlines()
    except OSError:
        return {}
    values = {}
    for line in lines:
        line = line.strip()
        if line.startswith("export "):
            line = line[len("export "):]
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        else:
            value = value.split(" #", 1)[0].strip()
        values[key.strip()] = value
    return values


def _write_env(path: Path, updates: dict):
    """Set ``updates`` in a ``.env`` file, keeping its other lines."""
    try:
        lines = Path(path).read_text().splitlines()
    except FileNotFoundError:
        lines = []
    remaining = dict(updates)
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("export "):
            stripped = stripped[len("export "):]
        key = stripped.partition("=")[0].strip()
        if "=" in stripped and not stripped.startswith("#") and key in remaining:
            lines[i] = f"{key}='{remaining.pop(key)}'"
    lines += [f"{key}='{value}'" for key, value in remaining.items()]
    _write_private(Path(path), "\n".join(lines) + "\n")


def _write_private(path: Path, text: str):
    """Write ``text`` to ``path``, readable by the current user only."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    os.chmod(path, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(text)


def _client_config(session: requests.Session):
    """Return ``(client_id, policy_id)`` from the account frontend, unless overridden by the environment."""
    client_id = os.environ.get(ENV_CLIENT_ID)
    policy_id = os.environ.get(ENV_POLICY_ID)
    if client_id and policy_id:
        return client_id, policy_id

    resp = session.get(CONFIG_SCRIPT_URL, timeout=TIMEOUT)
    resp.raise_for_status()
    start = resp.text.find("davinci:")
    if start < 0:
        raise AuthenticationError(
            f"Could not find the sign-in configuration in {CONFIG_SCRIPT_URL}. "
            f"Set {ENV_CLIENT_ID} and {ENV_POLICY_ID} to override it."
        )
    block = resp.text[start:start + 2000]

    def find(name):
        match = re.search(rf'\b{name}\s*:\s*"([^"]+)"', block)
        if not match:
            raise AuthenticationError(
                f"The sign-in configuration has no {name}. "
                f"Set {ENV_CLIENT_ID} and {ENV_POLICY_ID} to override it."
            )
        return match.group(1)

    return client_id or find("clientId"), policy_id or find("acrValues")


def _sign_in(username: str, password: str) -> str:
    """Run the OAuth authorization code + PKCE flow and return the access token."""
    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    state = secrets.token_urlsafe(24)

    # the identity provider links the steps through cookies, so they share one session
    with requests.Session() as session:
        session.headers.update(HEADERS)
        try:
            client_id, policy_id = _client_config(session)

            form = _json(session.get(
                AUTHORIZE_URL,
                params={
                    "client_id": client_id,
                    "response_type": "code",
                    "response_mode": "pi.flow",
                    "scope": "openid",
                    "state": state,
                    "nonce": secrets.token_urlsafe(24),
                    "code_challenge": challenge,
                    "code_challenge_method": "S256",
                    "acr_values": policy_id,
                },
                headers=PING_SDK_HEADERS,
                timeout=TIMEOUT,
            ), "starting the sign-in")
            try:
                submit_url = form["_links"]["next"]["href"]
                interaction_id = form["interactionId"]
                flow_id = form["id"]
                event_name = form["eventName"]
            except (KeyError, TypeError):
                raise AuthenticationError("Unexpected response when starting the sign-in.") from None
            if not isinstance(submit_url, str) or not submit_url.startswith(f"{IDP_ORIGIN}/"):
                raise AuthenticationError("Refusing to send credentials to an unexpected sign-in URL.")

            resp = session.post(
                submit_url,
                json={
                    "id": flow_id,
                    "eventName": event_name,
                    "interactionId": interaction_id,
                    "parameters": {
                        "eventType": "submit",
                        "data": {
                            "actionKey": "SIGNIN",
                            "formData": {"username": username, "password": password},
                        },
                    },
                },
                headers={**PING_SDK_HEADERS, "interactionId": interaction_id},
                timeout=TIMEOUT,
            )
            code = _authorization_code(resp, state)

            tokens = _json(session.post(
                TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "client_id": client_id,
                    "code": code,
                    "code_verifier": verifier,
                },
                timeout=TIMEOUT,
            ), "requesting the token")
        except requests.RequestException as exc:
            status = getattr(exc.response, "status_code", None)
            detail = f"HTTP {status}" if status else type(exc).__name__
            raise AuthenticationError(f"Sign-in request failed ({detail}).") from None

    access_token = tokens.get("access_token")
    if not isinstance(access_token, str) or not access_token:
        raise AuthenticationError("The sign-in returned no access token.")
    return access_token


def _json(resp: requests.Response, stage: str) -> dict:
    resp.raise_for_status()
    try:
        data = resp.json()
    except ValueError:
        data = None
    if not isinstance(data, dict):
        raise AuthenticationError(f"Unexpected response when {stage}.")
    return data


def _authorization_code(resp: requests.Response, state: str) -> str:
    try:
        data = resp.json()
    except ValueError:
        data = None
    if not isinstance(data, dict):
        resp.raise_for_status()
        raise AuthenticationError("Unexpected response from the sign-in.")
    if data.get("status") != "COMPLETED":
        # e.g. wrong credentials; the message is written for the user
        raise AuthenticationError(data.get("message") or f"Sign-in failed (HTTP {resp.status_code}).")
    result = data.get("authorizeResponse") or {}
    if result.get("state") != state:
        raise AuthenticationError("Sign-in failed: state mismatch in the response.")
    code = result.get("code")
    if not isinstance(code, str) or not code:
        raise AuthenticationError("Sign-in failed: no authorization code returned.")
    return code
