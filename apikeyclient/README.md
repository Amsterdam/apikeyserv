API Key client
==============

This client consists of a Django middleware that can be added
to a Django project to enable protection of a REST API
with an API key.

The middleware starts a thread that periodically calls a central
api key server to collect signing keys.

The API keys of incoming requests should be in a `X-Api-Key` header,
and are checked for validity, meaning that they are signed by one of the signing keys.

Two Django settings variables are used:

    - APIKEY_MANDATORY: an api key is mandatory in incoming requests
    - APIKEY_ENDPOINT: The url of the apikeyserver where the sigingkeys
      are collected


