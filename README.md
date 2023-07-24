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

For local development, create a virtualenv, only start the database container
then point to it in the environment and install dependencies:

    docker-compose up -d database
    export DATABASE_HOST=localhost
    pip install -r server/requirements.txt

For the first run, set up a user account and,
then issue the following commands to install and start the service:

    # docker-compose only
    docker-compose exec web bash

    cd server  # if not inside web image
    pytest .
    python manage.py makemigrations apikeys
    python manage.py migrate
    python manage.py createsuperuser  # Fill out the form
    python manage.py runserver  # if not inside web image

Now generate a signing key:

    openssl genpkey -algorithm ED25519 -outform PEM

Visit `http://localhost:8000/admin/` to add this signing key and start
adding API keys. Alternatively, a key can be added by piping the last command's
output through a management command:

    openssl genpkey -algorithm ED25519 -outform PEM |
        python manage.py addsigningkey /dev/stdin

apikeyserv can manage multiple signing keys to allow for key rotation.
Keys can be retired by unchecking their "active" flag.


Deployment
==========

For deployment the database credentials con be configured in the Django settings.
The database needs to be initialized with `python manage.py migrate` (from a running container).
A superuser (to access the `/admin`) can be added with `python manage.py createsuperuser`.

Client services
===============

This repository contains a client library for talking to apikeyserv.
Install it with:

    pip install datadiensten-apikeyclient

or:

    pip install 'git+https://github.com/Amsterdam/apikeyserv.git#subdirectory=apikeyclient'


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

Local testclient
================

A bare-bones Django client has been added tot test the Django middleware
locally. Assuming that a virtualenv has been created and activated:

    cd client
    pip install -r requirements.txt
    python __init__.py runserver localhost:nnnn  # port not conflicting with api key server

The Django settings variables `APIKEY_ENDPOINT` and `APIKEY_MANDATORY` (0 or 1)
that are needed for the middleware component can be configured as environment variables.


Copyright 2023 Gemeente Amsterdam. All rights reserved.
