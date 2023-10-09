from dataclasses import dataclass, field
import logging
from django.test import override_settings
import apikeyclient

from conftest import API_KEY



# Duck typing a request.
@dataclass
class DummyRequest:
    headers: dict = field(default_factory=dict)
    GET: dict = field(default_factory=dict)


def get_response(_request):
    _request


def test_logging_of_api_keys(caplog):
    """Prove that the API key is logged when a logger is configured.

    In the conftest an API_KEY_LOGGER is configured, so the API KEY needs
    to show up in the logs.
    """

    with override_settings(APIKEY_LOGGER="api-key-logger"):
        middleware = apikeyclient.ApiKeyMiddleware(get_response)
        with caplog.at_level(logging.INFO):
            middleware(DummyRequest(headers={"X-Api-Key": API_KEY}))
            assert caplog.records[0].getMessage() == f"API KEY: '{API_KEY}'"


def test_logging_of_api_keys_in_query_string(caplog):
    """Prove that the API key is logged when a logger is configured.

    In the conftest an API_KEY_LOGGER is configured, so the API KEY needs
    to show up in the logs.
    """

    with override_settings(APIKEY_LOGGER="api-key-logger"):
        middleware = apikeyclient.ApiKeyMiddleware(get_response)
        with caplog.at_level(logging.INFO):
            middleware(DummyRequest(GET={"x-api-key": API_KEY}))
            assert caplog.records[0].getMessage() == f"API KEY: '{API_KEY}'"


def test_no_logging_of_api_keys(caplog):
    """Prove that the API key is not logged when no logger configured."""

    middleware = apikeyclient.ApiKeyMiddleware(get_response)
    with caplog.at_level(logging.INFO):
        middleware(DummyRequest(headers={"X-Api-Key": API_KEY}))
        assert not caplog.records


