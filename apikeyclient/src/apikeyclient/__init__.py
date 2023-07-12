from datetime import datetime, timedelta
import logging
import threading

from django.conf import settings
from django.http import HttpRequest, HttpResponse
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

    Needs two settings:
    * APIKEY_ENDPOINT, to fetch signing keys from. Normally the /signingkeys/
      endpoint from apikeyserv.
    * APIKEY_MANDATORY, boolean that indicates whether API keys are required.
      If set to False, API keys are checked only when they are present, while
      requests without a key are still allowed.
    * APIKEY_LOCALKEYS, serialized json string with signing keys.
      If this setting is provided, keys will *not* be collected from APIKEY_ENDPOINT.
      Using this setting is only meant as a fallback mechanism, because deactivating
      a key needs a redeploy of the app that is using this middleware!
    """

    def __init__(self, get_response):
        self._client = self._fetch_client()
        self._get_response = get_response
        self._mandatory = bool(settings.APIKEY_MANDATORY)

    def __call__(self, request: HttpRequest):
        token = request.headers.get("X-Api-Key")
        if token is None and self._mandatory:
            return HttpResponse("API key missing", status=401)
        if token is not None:
            who = self._client.check(token)
            if who is None:
                return HttpResponse("invalid API key", status=402)
        return self._get_response(request)

    def _fetch_client(self):
        if settings.APIKEY_LOCALKEYS is not None:
            keyset = jwt.PyJWKSet(settings.APIKEY_LOCALKEYS)
            return LocalKeysClient([k.key for k in keyset.keys])
        else:
            return Client(settings.APIKEY_ENDPOINT)


def check_token(token, keys):
    """ Checks a token against list of signing keys."""
    for key in keys:
        try:
            dec = jwt.decode(token, key, algorithms="EdDSA")
            return dec["sub"]
        except (jwt.InvalidSignatureError, jwt.DecodeError):
            continue
    raise ValueError("API key not valid with any signing key")

class Client:
    _lock: threading.Lock
    _start: datetime
    _url: str

    def __init__(self, url: str):
        self._lock = threading.Lock()
        self._start = datetime.now()
        self._interval = KEY_FETCH_INTERVAL
        self._url = url

        self._keys = self._fetch_keys()

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
        return check_token(token, keys)

    def _fetch_keys(self):
        try:
            # Add timeout too avoid blocking this thread for too long.
            resp = requests.get(self._url, timeout=5)
            resp.raise_for_status()
            resp_json = resp.json()
            keyset = jwt.PyJWKSet(resp_json["keys"])
            return [k.key for k in keyset.keys]
        except Exception as e:
            logger.error("could not fetch JWKS from %s: %s", self._url, e)
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
