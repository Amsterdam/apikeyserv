import os

import jwt

from django.db import models


def secure_random():
    """Returns a cryptographically secure random 63-bit integer."""
    r = int.from_bytes(os.urandom(8), byteorder="little")
    # Drop one bit to please PostgreSQL.
    return r >> 1


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

    # Human-readable name of this key's owning organisation.
    organisation = models.CharField(max_length=256, null=False)

    # XXX We need to add an e-mail validator here.
    email = models.CharField(max_length=256, null=False)

    # Reason for requesting key (application name, ...).
    reason = models.CharField(max_length=512, default="", null=False)

    created = models.DateTimeField(auto_now_add=True, null=False)

    modified = models.DateTimeField(auto_now=True, null=False)

    expires = models.DateTimeField(blank=True, null=True)

    sent = models.BooleanField(default=False, null=False)


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
    keys = SigningKey.objects.filter(active=True).order_by("-created")
    return keys.first().private


def sign(obj: ApiKey) -> str:
    sign_key = get_signing_key()
    payload = {"sub": obj.id}
    if obj.expires is not None:
        payload["exp"] = obj.expires
    return jwt.encode(payload, sign_key, algorithm="EdDSA")
