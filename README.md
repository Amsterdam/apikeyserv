apikeyserv
==========

This program manages API keys for use by dataservices.

API keys are signed using this service's private key, so accepting services
only need this service's public key to confirm their validity, instead of
having to communicate with this service or its database.

The API keys are in JWT format so that services that deal with API keys can
use existing libraries for decoding them and verifying them against this
service's public key.


Setup and running
=================

The easy option:

    docker-compose up

For local development, only start the database,
then point to it in the environment and install dependencies:

    docker-compose up -d database
    export DATABASE_HOST=localhost
    pip install -r src/requirements.txt

For the first run, set up a user account and:
Then issue the following commands to install and start the service:

    # docker-compose only
    docker-compose exec web bash

    cd src
    python manage.py makemigrations apikeys
    python manage.py migrate
    python manage.py createsuperuser  # Fill out the form
    python manage.py runserver

Now generate a signing key:

    openssl genpkey -algorithm ED25519 -outform PEM

Visit `http://localhost:8000/admin/` to add this signing key and start
adding API keys. Alternatively, a key can be added by piping the last command's
output through a management command:

    openssl genpkey -algorithm ED25519 -outform PEM |
        python manage.py addsigningkey /dev/stdin

apikeyserv can manage multiple signing keys to allow for key rotation.
Keys can be retired by unchecking their "active" flag.


Client services
===============

Client services should check API keys against the public key(s) managed by
apikeyserv using PyJWT or another JWT library. They should periodically grab
the currently active keyset from apikeyserv's /signingkeys/ path, which serves
the active keys as a JSON Web Key Set (JWKS):

    >>> import jwt
    >>> from urllib.request import urlopen
    >>> response = urlopen("http://localhost:8000/signingkeys")
    >>> jwks = jwt.PyJWKSet.from_json(response.read())
    >>> pub_key = jwks.keys[0].key # In this case we assume it is signed with the first key
    >>> encoded_jwt = "xxxx.yyyy.zzzz"
    >>> jwt.decode(encoded_jwt, pub_key, algorithms="EdDSA")


Security and privacy
====================

API keys generated by this program do not contain personally identifying
information. Instead, they contain a numeric ID that is mapped to a name and
email address managed by apikeyserv.

The API keys should *not* be used to perform authorization checks
beyond those that give access to public data. (This means that requests
for protected data from DSO-API or other services require two JWTs, one for
the API key and one in the Authorization header.)
The use of public-key cryptography in this package serves mainly
to cut down on communications between the service that stores the keys
and applications that consume them, not to provide security.

For secure key distribution to consuming applications,
such applications should use a TLS connection to the service.


Copyright 2022 Gemeente Amsterdam. All rights reserved.
