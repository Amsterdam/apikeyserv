from apikeyclient import Client
from django.test import override_settings

from conftest import API_KEY, SIGNING_KEYS

def test_client(requests_mock):
    with override_settings(APIKEY_LOCALKEYS=None):
        url = "http://localhost/signingkeys"
        requests_mock.get(url, json={"keys": SIGNING_KEYS})
        client = Client(url)
        assert len(client._keys) == 1
        assert client.check(API_KEY) is not None
        assert client.check("wrong key") is None
