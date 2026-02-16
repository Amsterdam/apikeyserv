import apikeyclient
from http import HTTPStatus
from django.test import override_settings
import jwt
import pytest

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


@pytest.mark.parametrize(
    "mandatory, allow_empty", [(True, False), (False, True), (True, True), (False, False)]
)
def test_client_with_invalid_key_fails(mandatory, allow_empty):
    """Prove that middleware fails with a wrong key, for all combinations."""
    with override_settings(APIKEY_MANDATORY=mandatory, APIKEY_ALLOW_EMPTY=allow_empty):
        middleware = apikeyclient.ApiKeyMiddleware(get_response)
        res = middleware(DummyRequest(headers={"X-Api-Key": "invalid key"}))
        assert res.status_code == HTTPStatus.BAD_REQUEST
