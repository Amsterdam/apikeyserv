from datetime import datetime, timedelta
import logging
import threading

from django.conf import settings
from django.http import HttpRequest, HttpResponse
import jwt
import pause
import requests


logger = logging.getLogger(__name__)


class ApiKeyMiddleware:
    def __init__(self, get_response, mandatory: bool):
        self._client = Client(settings.APIKEY_ENDPOINT)
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


class Client:
    _lock: threading.Lock
    _start: datetime
    _url: str

    def __init__(self, url: str):
        self._lock = threading.Lock()
        self._start = datetime.now()
        self._url = url

        self._keys = self._fetch_keys()

        thr = threading.Thread(target=self._fetch_loop, daemon=True)
        thr.start()

    def check(self, token):
        """Returns the subject of the token, if it is valid."""
        with self._lock:
            keys = self._keys
        keys = keys or []

        for key in keys:
            try:
                dec = jwt.decode(token, key, algorithms="EdDSA")
                return dec["sub"]
            except jwt.InvalidSignatureError:
                continue
        raise ValueError("API key not valid with any signing key")

    def _fetch_keys(self):
        try:
            resp = requests.get(self._url).json()
            keyset = jwt.PyJWKSet(resp["keys"])
            return [k.key for k in keyset.keys]
        except Exception as e:
            logger.error("could not fetch JWKS from %s: %s", self._url, e)
            return None

    def _fetch_loop(self):
        t = self._start
        while True:
            t += timedelta(seconds=3600)
            pause.until(t)

            new_keys = self._fetch_keys()
            if new_keys is None:
                # If no keys could be fetched, keep the old ones.
                # We've already logged the error.
                continue
            with self._lock:
                self._keys = new_keys
