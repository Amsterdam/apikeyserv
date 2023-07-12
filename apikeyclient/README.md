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

    - APIKEY_MANDATORY: an api key is mandatory in incoming requests
    - APIKEY_ENDPOINT: The url of the apikeyserver where the sigingkeys
      are collected (path in the url is `/signingkeys/`)


