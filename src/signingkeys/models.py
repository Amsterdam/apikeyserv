from django.db import models


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
