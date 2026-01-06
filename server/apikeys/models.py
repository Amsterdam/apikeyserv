from datetime import datetime, timedelta
import json
import os
from django.forms import model_to_dict

import jwt

from django.db import models


def get_expiry_datetime():
    return datetime.today() + timedelta(days=365)


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
    contactperson_1_name = models.CharField(
        max_length=256, null=True, blank=True, verbose_name="Contactpersoon"
    )
    email_1 = models.EmailField(
        max_length=256,
        null=False,
        blank=False,
        default="",
        verbose_name="E-mailadres",
    )
    contactperson_2_name = models.CharField(
        max_length=256, null=True, blank=True, verbose_name="Tweede contactpersoon"
    )
    email_2 = models.EmailField(
        max_length=256, null=True, blank=True, verbose_name="Tweede e-mailadres"
    )
    # Human-readable name of this key's owning organisation.
    organisation = models.CharField(max_length=256, null=False, verbose_name="Organisatie")
    department = models.CharField(max_length=256, null=True, blank=True, verbose_name="Afdeling")
    created = models.DateTimeField(auto_now_add=True, null=False)
    modified = models.DateTimeField(auto_now=True, null=False)
    expires = models.DateTimeField(blank=True, null=True, default=get_expiry_datetime)
    sent = models.BooleanField(default=False, null=False)

    def as_json(self):
        """Returns the apikey fields as json."""
        api_key_dict = model_to_dict(self)
        api_key_dict["apikey"] = sign(self)
        return api_key_dict

    @property
    def sub(self):
        """Returns the subject of the key as a string."""
        return str(self.id)


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
    payload = {"sub": obj.sub}
    if obj.expires is not None:
        payload["exp"] = obj.expires
    return jwt.encode(payload, sign_key, algorithm="EdDSA")
