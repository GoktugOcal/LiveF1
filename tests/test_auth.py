"""Tests for livef1.auth (F1 account sign-in). Fully mocked, no network."""
import base64
import inspect
import json
import stat
import time
from unittest.mock import MagicMock, patch

import pytest
import requests

from livef1 import auth
from livef1.adapters.livetimingf1_adapter import LivetimingF1adapters
from livef1.config import _settings, configure
from livef1.utils.exceptions import AuthenticationError


def make_jwt(claims):
    payload = base64.urlsafe_b64encode(json.dumps(claims).encode()).rstrip(b"=").decode()
    return f"eyJhbGciOiJub25lIn0.{payload}.sig"


def make_access_token(expires_in=3600):
    subscription = make_jwt({"exp": time.time() + expires_in})
    return make_jwt({"subscriptionToken": subscription}), subscription


def response(json_data=None, text="", status=200):
    resp = MagicMock()
    resp.status_code = status
    resp.text = text
    if json_data is None:
        resp.json.side_effect = ValueError("no json")
    else:
        resp.json.return_value = json_data
    if status >= 400:
        resp.raise_for_status.side_effect = requests.HTTPError(response=resp)
    return resp


class FakeSession:
    """Stands in for requests.Session; responses may be callables receiving the session."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.headers = {}
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def _next(self, method, url, kwargs):
        self.calls.append((method, url, kwargs))
        item = self.responses.pop(0)
        return item(self) if inspect.isfunction(item) else item

    def get(self, url, **kwargs):
        return self._next("GET", url, kwargs)

    def post(self, url, **kwargs):
        return self._next("POST", url, kwargs)


SCRIPT = 'x={a:1},davinci:{clientId:"client-123",acrValues:"policy-456",scope:"openid"}'
FORM = {
    "_links": {"next": {"href": "https://id.formula1.com/davinci/next"}},
    "interactionId": "interaction",
    "id": "flow",
    "eventName": "continue",
}


def completed(session):
    state = session.calls[1][2]["params"]["state"]
    return response({"status": "COMPLETED", "authorizeResponse": {"state": state, "code": "the-code"}})


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    for name in ("F1_USERNAME", "F1_PASSWORD", "LIVEF1_F1_CLIENT_ID", "LIVEF1_F1_POLICY_ID"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(auth, "_token", None)
    saved = dict(_settings)
    configure(auth_token_path=tmp_path / "token.json", auth_env_path=tmp_path / ".env")
    yield tmp_path
    _settings.clear()
    _settings.update(saved)


# --- client config ---

def test_client_config_from_script():
    session = FakeSession([response(text=SCRIPT)])
    assert auth._client_config(session) == ("client-123", "policy-456")


def test_client_config_missing_field():
    session = FakeSession([response(text='davinci:{clientId:"client-123"}')])
    with pytest.raises(AuthenticationError, match="acrValues"):
        auth._client_config(session)


def test_client_config_env_override(monkeypatch):
    monkeypatch.setenv("LIVEF1_F1_CLIENT_ID", "env-client")
    monkeypatch.setenv("LIVEF1_F1_POLICY_ID", "env-policy")
    session = FakeSession([])
    assert auth._client_config(session) == ("env-client", "env-policy")
    assert session.calls == []


# --- sign-in flow ---

def test_sign_in_success():
    access_token, _ = make_access_token()
    session = FakeSession([
        response(text=SCRIPT), response(FORM), completed, response({"access_token": access_token}),
    ])
    with patch.object(auth.requests, "Session", return_value=session):
        assert auth._sign_in("user@example.com", "pw") == access_token

    params = session.calls[1][2]["params"]
    assert params["client_id"] == "client-123"
    assert params["acr_values"] == "policy-456"
    assert params["code_challenge_method"] == "S256"
    form_data = session.calls[2][2]["json"]["parameters"]["data"]["formData"]
    assert form_data == {"username": "user@example.com", "password": "pw"}
    token_request = session.calls[3][2]["data"]
    assert token_request["code"] == "the-code"
    assert len(token_request["code_verifier"]) >= 43


def test_sign_in_wrong_password():
    session = FakeSession([
        response(text=SCRIPT), response(FORM),
        response({"status": "FAILED", "message": "Invalid username or password"}, status=400),
    ])
    with patch.object(auth.requests, "Session", return_value=session):
        with pytest.raises(AuthenticationError, match="Invalid username or password"):
            auth._sign_in("user@example.com", "wrong")


def test_sign_in_state_mismatch():
    session = FakeSession([
        response(text=SCRIPT), response(FORM),
        response({"status": "COMPLETED", "authorizeResponse": {"state": "other", "code": "c"}}),
    ])
    with patch.object(auth.requests, "Session", return_value=session):
        with pytest.raises(AuthenticationError, match="state mismatch"):
            auth._sign_in("user@example.com", "pw")


def test_sign_in_refuses_foreign_submit_url():
    form = {**FORM, "_links": {"next": {"href": "https://evil.example.com/collect"}}}
    session = FakeSession([response(text=SCRIPT), response(form)])
    with patch.object(auth.requests, "Session", return_value=session):
        with pytest.raises(AuthenticationError, match="unexpected sign-in URL"):
            auth._sign_in("user@example.com", "pw")
    assert len(session.calls) == 2


# --- token decoding ---

def test_token_from_access_token():
    access_token, subscription = make_access_token()
    token = auth.F1Token.from_access_token(access_token)
    assert token.value == subscription
    assert not token.expired
    assert token.header == {"Authorization": f"Bearer {subscription}"}
    assert subscription not in repr(token)


def test_token_missing_subscription_claim():
    with pytest.raises(AuthenticationError, match="F1TV subscription"):
        auth.F1Token.from_access_token(make_jwt({"sub": "x"}))


def test_token_expired_within_margin():
    token = auth.F1Token(value="v", expires_at=time.time() + auth.EXPIRY_MARGIN - 1)
    assert token.expired


# --- login and token file ---

def test_login_saves_and_reuses_token(isolated, monkeypatch):
    monkeypatch.setenv("F1_USERNAME", "user@example.com")
    monkeypatch.setenv("F1_PASSWORD", "pw")
    access_token, subscription = make_access_token()
    with patch.object(auth, "_sign_in", return_value=access_token) as sign_in:
        first = auth.login()
        monkeypatch.setattr(auth, "_token", None)
        second = auth.login()

    assert sign_in.call_count == 1
    assert first.value == second.value == subscription
    token_file = isolated / "token.json"
    assert json.loads(token_file.read_text())["token"] == subscription
    assert stat.S_IMODE(token_file.stat().st_mode) == 0o600


def test_login_force_signs_in_again(monkeypatch):
    monkeypatch.setenv("F1_USERNAME", "user@example.com")
    monkeypatch.setenv("F1_PASSWORD", "pw")
    with patch.object(auth, "_sign_in", side_effect=[make_access_token()[0], make_access_token()[0]]) as sign_in:
        auth.login()
        auth.login(force=True)
    assert sign_in.call_count == 2


def test_login_without_saving_token(isolated, monkeypatch):
    monkeypatch.setenv("F1_USERNAME", "user@example.com")
    monkeypatch.setenv("F1_PASSWORD", "pw")
    with patch.object(auth, "_sign_in", return_value=make_access_token()[0]):
        token = auth.login(save_token=False)
    assert not (isolated / "token.json").exists()
    assert auth.auth_header() == token.header


def test_login_custom_token_path(isolated, monkeypatch):
    monkeypatch.setenv("F1_USERNAME", "user@example.com")
    monkeypatch.setenv("F1_PASSWORD", "pw")
    path = isolated / "nested" / "my_token.json"
    with patch.object(auth, "_sign_in", return_value=make_access_token()[0]):
        auth.login(token_path=path)
    assert path.exists()
    assert not (isolated / "token.json").exists()


def test_corrupt_token_file_signs_in_again(isolated, monkeypatch):
    monkeypatch.setenv("F1_USERNAME", "user@example.com")
    monkeypatch.setenv("F1_PASSWORD", "pw")
    (isolated / "token.json").write_text("{not json")
    with patch.object(auth, "_sign_in", return_value=make_access_token()[0]) as sign_in:
        auth.login()
    assert sign_in.call_count == 1


def test_logout_removes_token(isolated, monkeypatch):
    monkeypatch.setenv("F1_USERNAME", "user@example.com")
    monkeypatch.setenv("F1_PASSWORD", "pw")
    (isolated / ".env").write_text("F1_USERNAME=user@example.com\n")
    with patch.object(auth, "_sign_in", return_value=make_access_token()[0]):
        auth.login()
    auth.logout()
    assert not (isolated / "token.json").exists()
    assert auth.auth_header() == {}
    assert (isolated / ".env").exists()


# --- .env credentials ---

def test_credentials_from_env_file(isolated):
    (isolated / ".env").write_text(
        "# comment\nOTHER=1\nexport F1_USERNAME=user@example.com\nF1_PASSWORD='p#ss word'\n"
    )
    with patch.object(auth, "_sign_in", return_value=make_access_token()[0]) as sign_in:
        auth.login()
    sign_in.assert_called_once_with("user@example.com", "p#ss word")


def test_prompted_credentials_are_saved(isolated, monkeypatch):
    env_file = isolated / ".env"
    env_file.write_text("OTHER=1\nF1_USERNAME=old@example.com\n")
    monkeypatch.setattr(auth, "_can_prompt", lambda: True)
    monkeypatch.setattr("builtins.input", lambda prompt: "unused")
    monkeypatch.setattr(auth.getpass, "getpass", lambda prompt: "secret")
    with patch.object(auth, "_sign_in", return_value=make_access_token()[0]) as sign_in:
        auth.login()

    sign_in.assert_called_once_with("old@example.com", "secret")
    assert env_file.read_text() == "OTHER=1\nF1_USERNAME=old@example.com\nF1_PASSWORD='secret'\n"
    assert stat.S_IMODE(env_file.stat().st_mode) == 0o600
    assert auth._read_env(env_file)["F1_PASSWORD"] == "secret"


def test_prompted_key_updated_in_place(isolated):
    env_file = isolated / ".env"
    env_file.write_text("F1_USERNAME=old\nOTHER=1\n")
    auth._write_env(env_file, {"F1_USERNAME": "new"})
    assert env_file.read_text() == "F1_USERNAME='new'\nOTHER=1\n"


def test_failed_login_saves_nothing(isolated, monkeypatch):
    monkeypatch.setattr(auth, "_can_prompt", lambda: True)
    monkeypatch.setattr("builtins.input", lambda prompt: "user@example.com")
    monkeypatch.setattr(auth.getpass, "getpass", lambda prompt: "typo")
    with patch.object(auth, "_sign_in", side_effect=AuthenticationError("Invalid username or password")):
        with pytest.raises(AuthenticationError):
            auth.login()
    assert not (isolated / ".env").exists()
    assert not (isolated / "token.json").exists()


def test_no_credentials_without_tty(monkeypatch):
    monkeypatch.setattr(auth, "_can_prompt", lambda: False)
    with pytest.raises(AuthenticationError, match="F1_USERNAME"):
        auth.login()


# --- live timing adapter ---

def test_adapter_attaches_token(monkeypatch):
    token = auth.F1Token(value="abc", expires_at=time.time() + 3600)
    monkeypatch.setattr(auth, "_token", token)
    with patch("livef1.adapters.livetimingf1_adapter.requests.get", return_value=response(text="{}")) as get:
        get.return_value.content = b"{}"
        LivetimingF1adapters().get("2026/Index.json")
    assert get.call_args.kwargs["headers"]["Authorization"] == "Bearer abc"


def test_adapter_signs_in_once_on_401():
    token = auth.F1Token(value="fresh", expires_at=time.time() + 3600)
    ok = response(text="{}")
    ok.content = b"{}"
    with patch("livef1.adapters.livetimingf1_adapter.requests.get", side_effect=[response(status=401), ok]) as get, \
            patch("livef1.adapters.livetimingf1_adapter.login", return_value=token) as login:
        assert LivetimingF1adapters().get("2026/Index.json") == "{}"
    login.assert_called_once_with(force=True)
    assert get.call_args.kwargs["headers"]["Authorization"] == "Bearer fresh"


def test_adapter_raises_without_credentials(monkeypatch):
    monkeypatch.setattr(auth, "_can_prompt", lambda: False)
    with patch("livef1.adapters.livetimingf1_adapter.requests.get", return_value=response(status=403)) as get:
        with pytest.raises(AuthenticationError, match="F1_USERNAME"):
            LivetimingF1adapters().get("2026/Index.json")
    assert get.call_count == 1
