This program manages API keys for use by dataservices.

API keys are signed using this service's private key, so accepting services
only need this service's public key to confirm their validity, instead of
having to communicate with this service or its database.

The API keys are in JWT format so that services that deal with API keys can
use existing libraries for decoding them and verifying them against this
service's public key. They should *not* be used to perform authorization
checks beyond those that give access to public data. That means that requests
for protected data from DSO-API or other services require two JWTs, one for
the API key and one in the Authorization header.

Running:

    cd src
    python manage.py makemigrations apikeys signingkeys
    python manage.py migrate
    python manage.py createsuperuser  # Fill out the form
    python manage.py runserver
    # Generate a signing key:
    openssl genpkey -algorithm ED25519 -outform PEM

Now visit `http://localhost:8000/admin/` to add this signing key and start
adding API keys.


Copyright 2022 Gemeente Amsterdam. All rights reserved.
