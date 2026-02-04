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
------------

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
------------------

(For developers)

We use GitHub pull requests. If your PR should produce a new release of
schema-tools, make sure one of the commit increments the version number in
``apikeyclient/pyproject.toml`` appropriately and add an entry to the top of the
``CHANGELOG.md`` file. Then,

* Merge the PR in GitHub, after review.
* Pull the latest main branch from GitHub:
  ``git fetch && git checkout origin/main``.
* Tag the release X.Y.Z with ``git tag -a vX.Y.Z -m "Bump to vX.Y.Z"``.
* Push the tag to GitHub with ``git push origin --tags``.
* The ``publish-to-pypi`` workflow will automatically publish the release.
