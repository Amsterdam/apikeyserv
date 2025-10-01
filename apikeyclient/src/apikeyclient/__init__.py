from datetime import datetime, timedelta
from http import HTTPStatus
import logging
import threading

from django.conf import settings
from django.http import HttpRequest, JsonResponse
import jwt
import pause
import requests


logger = logging.getLogger(__name__)

KEY_FETCH_INTERVAL = 3600  # in seconds


class ApiKeyMiddleware:
    """Django middleware that check API keys in the X-Api-Key header.

    This middleware launches a daemon thread that periodically connects to
    the API key server to fetch the public signing keys. That means it can
    check API keys without connectivity to the API key server.

    Needs a number of settings:
    * APIKEY_ENDPOINT, to fetch signing keys from. Normally the /signingkeys/
      endpoint from apikeyserv.
    * APIKEY_MANDATORY, boolean that indicates whether API keys are required.
      If set to False, API keys are checked only when they are present, while
      requests without a key are still allowed.
    * APIKEY_ALLOW_EMPTY, boolean indicating that an empty API key is allowed,
      so, only the key needs to be in a header, it can be empty.
    * APIKEY_ALLOW_PATH_PREFIX_WHITELIST, list of pathprefixes that are always allowed
    * APIKEY_LOCALKEYS, serialized json string with signing keys.
      If this setting is provided, keys will *not* be collected from APIKEY_ENDPOINT.
      Using this setting is only meant as a fallback mechanism, because deactivating
      a key needs a redeploy of the app that is using this middleware!
    * APIKEY_LOGGER, the logger that will be used to log the api key request header.
    """

    def __init__(self, get_response):
        self._client = self._fetch_client()
        self._get_response = get_response
        self._mandatory = bool(settings.APIKEY_MANDATORY)
        self._allow_empty = bool(settings.APIKEY_ALLOW_EMPTY)
        self._allow_path_prefix_whitelist = getattr(
            settings, "APIKEY_ALLOW_PATH_PREFIX_WHITELIST", ("/v1/wfs",)
        )
        self._api_key_logger = self._fetch_api_key_logger()

    def __call__(self, request: HttpRequest):
        # We skip api key checks for browser-based access
        # We deliberately make this a very simple check, because using
        # the full user agent for checking (e.g. with django-user-agents)
        # is overkill, and also a bit brittle (too many user agents to keep track of).
        if request.path.startswith(tuple(self._allow_path_prefix_whitelist)):
            return self._get_response(request)

        if request.headers.get("User-Agent", "").startswith("Mozilla"):
            return self._get_response(request)

        token = request.headers.get("X-Api-Key")
        if token is None:
            token = request.GET.get("x-api-key")
            if token:
                # Make a copy of request.GET, to mutate it
                request.GET = request.GET.copy()
                # we need to get rid of the query param, DSO API does not recognize it
                del request.GET["x-api-key"]
        if token is None and self._mandatory:
            return JsonResponse({"message": "API key missing"}, status=HTTPStatus.UNAUTHORIZED)
        if token is not None:
            if token.strip() == "" and self._allow_empty:
                return self._get_response(request)
            # Log the API KEY, also if it is not valid.
            self._log_api_key(token)
            who = self._client.check(token)
            if who is None:
                return JsonResponse({"message": "invalid API key"}, status=HTTPStatus.BAD_REQUEST)
        return self._get_response(request)

    def _fetch_client(self):
        apikey_localkeys = getattr(settings, "APIKEY_LOCALKEYS", None)
        if apikey_localkeys is not None:
            keyset = jwt.PyJWKSet(apikey_localkeys)
            return LocalKeysClient([k.key for k in keyset.keys])
        else:
            return Client(settings.APIKEY_ENDPOINT)

    def _fetch_api_key_logger(self):
        """Fetching the logger at instantiation for easier patching during tests."""
        api_key_logger = None
        if (logger_name := getattr(settings, "APIKEY_LOGGER", None)) is not None:
            api_key_logger = logging.getLogger(logger_name)
        return api_key_logger

    def _log_api_key(self, token):
        if self._api_key_logger is not None:
            self._api_key_logger.info("API KEY: %r", token)


def check_token(token, keys):
    """Checks a token against list of signing keys."""
    for key in keys:
        try:
            dec = jwt.decode(token, key, algorithms="EdDSA", options={'verify_exp': False})
            return dec["sub"]
        except (jwt.InvalidSignatureError, jwt.DecodeError, jwt.ExpiredSignatureError):
            continue
    logger.error("API key is not valid with any signing key or has expired.")
    return None


class Client:
    _lock: threading.Lock
    _start: datetime
    _url: str

    def __init__(self, url: str):
        self._lock = threading.Lock()
        self._start = datetime.now()
        self._interval = KEY_FETCH_INTERVAL
        self._url = url

        self._keys = self._fetch_keys(bailoutIfNoConnection=True)

        # If no keys can be fetched we keep checking with a shorter _interval
        # until keys are found.
        if self._keys is None:
            self._interval = 5

        thr = threading.Thread(target=self._fetch_loop, daemon=True)
        thr.start()

    def check(self, token):
        """Returns the subject of the token, if it is valid."""
        with self._lock:
            keys = self._keys
        keys = keys or []
        if not keys:
            logger.warning("No signing keys available!")
        return check_token(token, keys)

    def _fetch_keys(self, bailoutIfNoConnection=False):
        try:
            # Add timeout too avoid blocking this thread for too long.
            resp = requests.get(self._url, timeout=5)
            resp.raise_for_status()
            resp_json = resp.json()
            keyset = jwt.PyJWKSet(resp_json["keys"])
            return [k.key for k in keyset.keys]
        except Exception as e:
            logger.error("could not fetch JWKS from %s: %s", self._url, e)
            # If keys are mandatory, but no signing keys can be fetched,
            # we should not be able to continue.
            if bool(settings.APIKEY_MANDATORY) and bailoutIfNoConnection:
                logger.error(
                    "Because settings.APIKEY_MANDATORY is True, "
                    "and we cannot connect to the API Key server, we bail out here!"
                )
                raise
            return None

    def _fetch_loop(self):
        t = self._start
        while True:
            t += timedelta(seconds=self._interval)
            pause.until(t)

            new_keys = self._fetch_keys()
            if new_keys is None:
                # If no keys could be fetched, keep the old ones.
                # We've already logged the error.
                continue
            with self._lock:
                self._interval = KEY_FETCH_INTERVAL
                self._keys = new_keys


class LocalKeysClient:
    def __init__(self, keys):
        self._keys = keys

    def check(self, token):
        return check_token(token, self._keys)
