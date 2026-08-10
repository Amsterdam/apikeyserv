import apikeyclient
from http import HTTPStatus
from django.test import override_settings
import jwt
import pytest
import threading

from conftest import API_KEY, SIGNING_KEYS
from utils import DummyRequest, get_response


def test_check_token():
    keyset = jwt.PyJWKSet(SIGNING_KEYS)
    sub = apikeyclient.check_token(API_KEY, keyset)
    assert sub is not None


def test_client_with_remote_signing_keys(requests_mock):
    """Prove that client works with remote keys."""
    with override_settings(APIKEY_LOCALKEYS=None):
        url = "http://localhost/signingkeys"
        requests_mock.get(url, json={"keys": SIGNING_KEYS})
        client = apikeyclient.Client(url)
        assert len(client._keys) == 1
        assert client.check(API_KEY) is not None
        assert client.check("wrong key") is None


def test_client_with_empty_key_succeeds():
    """Prove that middleware works with an empty key, if config allows it."""
    with override_settings(APIKEY_MANDATORY=True, APIKEY_ALLOW_EMPTY=True):
        middleware = apikeyclient.ApiKeyMiddleware(get_response)
        res = middleware(DummyRequest(headers={"X-Api-Key": ""}))
        assert res.status_code == HTTPStatus.OK


def test_client_with_allowed_prefix_succeeds():
    """Prove that middleware works with path_prefix that is allowed."""
    with override_settings(APIKEY_MANDATORY=True, APIKEY_ALLOW_PATH_PREFIX_WHITELIST=["/v1/wfs"]):
        middleware = apikeyclient.ApiKeyMiddleware(get_response)
        res = middleware(DummyRequest(headers={"X-Api-Key": ""}, path="/v1/wfs/some-dataset"))
        assert res.status_code == HTTPStatus.OK


def test_client_with_unallowed_prefix_fails():
    """Prove that middleware does not work with path_prefix that is not allowed."""
    with override_settings(APIKEY_MANDATORY=True, APIKEY_ALLOW_PATH_PREFIX_WHITELIST=["/v1/wfs"]):
        middleware = apikeyclient.ApiKeyMiddleware(get_response)
        res = middleware(
            DummyRequest(headers={"X-Api-Key": "invalid key"}, path="/v1/some-dataset/some-table")
        )
        assert res.status_code == HTTPStatus.BAD_REQUEST


def test_browser_requests_bypass_api_key_check():
    with override_settings(APIKEY_MANDATORY=True):
        middleware = apikeyclient.ApiKeyMiddleware(get_response)
        res = middleware(DummyRequest(headers={"User-Agent": "Mozilla/5.0", "X-Api-Key": "invalid"}))
        assert res.status_code == HTTPStatus.OK


def test_missing_key_fails_when_mandatory():
    with override_settings(APIKEY_MANDATORY=True):
        middleware = apikeyclient.ApiKeyMiddleware(get_response)
        res = middleware(DummyRequest())
        assert res.status_code == HTTPStatus.UNAUTHORIZED


def test_query_string_key_is_removed_after_validation():
    middleware = apikeyclient.ApiKeyMiddleware(get_response)
    request = DummyRequest(GET={"x-api-key": API_KEY, "other": "value"})

    res = middleware(request)

    assert res.status_code == HTTPStatus.OK
    assert "x-api-key" not in request.GET
    assert request.GET["other"] == "value"


def test_middleware_fetches_remote_client(requests_mock):
    with override_settings(APIKEY_LOCALKEYS=None, APIKEY_ENDPOINT="http://localhost/signingkeys"):
        url = "http://localhost/signingkeys"
        requests_mock.get(url, json={"keys": SIGNING_KEYS})

        middleware = apikeyclient.ApiKeyMiddleware(get_response)

        assert isinstance(middleware._client, apikeyclient.Client)


def test_check_token_invalid_returns_none(caplog):
    keyset = jwt.PyJWKSet(SIGNING_KEYS)

    with caplog.at_level("ERROR"):
        assert apikeyclient.check_token("invalid token", [k.key for k in keyset.keys]) is None


def test_client_check_without_keys_warns(caplog):
    client = apikeyclient.Client.__new__(apikeyclient.Client)
    client._lock = threading.Lock()
    client._keys = None

    with caplog.at_level("WARNING"):
        assert client.check(API_KEY) is None
        assert "No signing keys available!" in caplog.text


def test_fetch_keys_returns_none_when_request_fails(monkeypatch):
    client = apikeyclient.Client.__new__(apikeyclient.Client)
    client._url = "http://localhost/signingkeys"

    def raise_error(*_args, **_kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(apikeyclient.requests, "get", raise_error)

    with override_settings(APIKEY_MANDATORY=False):
        assert client._fetch_keys() is None


def test_fetch_keys_raises_when_mandatory_and_initial_fetch_fails(monkeypatch):
    client = apikeyclient.Client.__new__(apikeyclient.Client)
    client._url = "http://localhost/signingkeys"

    def raise_error(*_args, **_kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(apikeyclient.requests, "get", raise_error)

    with override_settings(APIKEY_MANDATORY=True):
        with pytest.raises(RuntimeError):
            client._fetch_keys(bailoutIfNoConnection=True)


def test_client_retries_quickly_when_initial_key_fetch_fails(monkeypatch):
    started = []

    class FakeThread:
        def __init__(self, target, daemon):
            self.target = target
            self.daemon = daemon

        def start(self):
            started.append(True)

    monkeypatch.setattr(apikeyclient.Client, "_fetch_keys", lambda self, bailoutIfNoConnection=False: None)
    monkeypatch.setattr(apikeyclient.threading, "Thread", FakeThread)

    with override_settings(APIKEY_MANDATORY=False):
        client = apikeyclient.Client("http://localhost/signingkeys")

    assert client._interval == 5
    assert started == [True]


def test_fetch_loop_keeps_old_keys_when_refresh_fails(monkeypatch):
    client = apikeyclient.Client.__new__(apikeyclient.Client)
    client._start = apikeyclient.datetime.now()
    client._interval = 5
    client._lock = threading.Lock()
    client._keys = ["existing"]

    pause_calls = iter([None, StopIteration()])
    monkeypatch.setattr(apikeyclient.pause, "until", lambda _when: _raise_or_pass(pause_calls))
    client._fetch_keys = lambda: None

    with pytest.raises(StopIteration):
        client._fetch_loop()

    assert client._keys == ["existing"]
    assert client._interval == 5


def test_fetch_loop_updates_keys_when_refresh_succeeds(monkeypatch):
    client = apikeyclient.Client.__new__(apikeyclient.Client)
    client._start = apikeyclient.datetime.now()
    client._interval = 5
    client._lock = threading.Lock()
    client._keys = ["existing"]

    pause_calls = iter([None, StopIteration()])
    monkeypatch.setattr(apikeyclient.pause, "until", lambda _when: _raise_or_pass(pause_calls))
    client._fetch_keys = lambda: ["updated"]

    with pytest.raises(StopIteration):
        client._fetch_loop()

    assert client._keys == ["updated"]
    assert client._interval == apikeyclient.KEY_FETCH_INTERVAL


def _raise_or_pass(results):
    result = next(results)
    if isinstance(result, BaseException):
        raise result


@pytest.mark.parametrize(
    "mandatory, allow_empty", [(True, False), (False, True), (True, True), (False, False)]
)
def test_client_with_invalid_key_fails(mandatory, allow_empty):
    """Prove that middleware fails with a wrong key, for all combinations."""
    with override_settings(APIKEY_MANDATORY=mandatory, APIKEY_ALLOW_EMPTY=allow_empty):
        middleware = apikeyclient.ApiKeyMiddleware(get_response)
        res = middleware(DummyRequest(headers={"X-Api-Key": "invalid key"}))
        assert res.status_code == HTTPStatus.BAD_REQUEST
