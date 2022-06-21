import os

import jwt

from django.db import models


def secure_random():
    """Returns a cryptographically secure random 64-bit integer."""
    return int.from_bytes(os.urandom(8), byteorder="little")


class ApiKey(models.Model):
    """Data and metadata for an API key."""

    # The id gets put in the JWT, so we don't have to send the name or
    # email address to any place that might log it, and so that we can
    # change names or email addresses without changing the API key (JWT).
    #
    # The id is randomized so we don't leak how many keys there are.
    #
    # Making this the primary key ensures uniqueness.
    id = models.BigIntegerField(default=secure_random, primary_key=True)

    # Human-readable name of this key's owner.
    name = models.CharField(max_length=256, null=False)

    email = models.CharField(max_length=256, null=False)

    created = models.DateTimeField(auto_now_add=True, null=False)

    modified = models.DateTimeField(auto_now=True, null=False)

    expires = models.DateTimeField(blank=True, null=True)


class SigningKey(models.Model):
    """A signing key pair."""

    # The private key, in PEM+PKCS#8 format.
    private = models.TextField(null=False)

    active = models.BooleanField(default=True, null=False)

    created = models.DateTimeField(auto_now_add=True, null=False)


def get_signing_key() -> str:
    """Returns the current signing key's private part.

    The current signing key is the newest key that is marked active.
    """
    return SigningKey.objects.filter(active=True).order_by("-created").first().private


def sign(obj: ApiKey) -> str:
    sign_key = get_signing_key()
    payload = {"sub": obj.id}
    if obj.expires is not None:
        payload["exp"] = obj.expires
    return jwt.encode(payload, sign_key, algorithm="EdDSA")
