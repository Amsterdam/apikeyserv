import os

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