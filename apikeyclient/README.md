API Key client
==============

This client consists of a Django middleware that can be added
to a Django project to enable protection of a REST API
with an API key.

The middleware starts a thread that periodically calls a central
api key server to collect signing keys.

The API keys of incoming requests should be in a `X-Api-Key` header,
and are checked for validity, meaning that they are signed by one of the signing keys.


Installation
============

Pip install the middleware package in your project with:

    pip install datadiensten-apikeyclient

Install the middelware in the settings.py of your Django settings with:

    MIDDLEWARE=(
        ...
        "apikeyclient.ApiKeyMiddleware",
    )

And add the following constants to you Django settings:

    - APIKEY_ENDPOINT: The url of the apikeyserver where the sigingkeys
      are collected (path in the url is `/signingkeys/`)
    - APIKEY_MANDATORY: an api key is mandatory in incoming requests (default: false)
    - APIKEY_ALLOW_EMPTY: an api key can be empty (default: true)
    - APIKEY_LOCALKEYS: serialized json string with signingkeys,
      if defined, keys will *not* be collected from APIKEY_ENDPOINT


If for some reason the middelware cannot be configured to access
the api key server to collect the signing keys, it is possible to
put these keys in the `APIKEY_LOCALKEYS` settings variable.
This variable should contain a serialized json string with signing keys,
e.g. `[{"kty": "OKP", "alg": "EdDSA", "crv": "Ed25519", "x": "<signing key>"}]`.


Publishing to PyPI
==================

The process to publish the API Key client middleware package to PyPI has been described on the Datadiensten ADO Wiki.

