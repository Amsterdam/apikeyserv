import apikeyclient
from http import HTTPStatus
from django.test import override_settings
import pytest

from conftest import API_KEY, SIGNING_KEYS
from utils import DummyRequest, get_response


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


@pytest.mark.parametrize(
    "mandatory, allow_empty", [(True, False), (False, True), (True, True), (False, False)]
)
def test_client_with_wrong_key_fails(mandatory, allow_empty):
    """Prove that middleware fails with a wrong key, for all combinations."""
    with override_settings(APIKEY_MANDATORY=mandatory, APIKEY_ALLOW_EMPTY=allow_empty):
        middleware = apikeyclient.ApiKeyMiddleware(get_response)
        res = middleware(DummyRequest(headers={"X-Api-Key": "wrong key"}))
        assert res.status_code == HTTPStatus.BAD_REQUEST
