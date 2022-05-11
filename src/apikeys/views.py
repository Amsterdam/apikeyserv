import json

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from django.http import HttpResponse
import logging
from typing import Optional

from .display import jwk
from .models import SigningKey


logger = logging.getLogger(__file__)


def index(request):
    """Renders all active signing keys as a JWKS."""
    active_keys = SigningKey.objects.filter(active=True)

    keyset = []

    for priv, id in active_keys.values_list("private", "id"):
        pub = public_key(priv, id)
        if pub is None:
            continue

        keyset.append(jwk(pub))

    jwks = {"keys": keyset}
    return HttpResponse(json.dumps(jwks), content_type="application/json")


def public_key(priv_pem: str, id: int) -> Optional[Ed25519PublicKey]:
    """Returns the public key  for the private key priv_pem.

    The private key must be in PEM format.

    The id is the database id, used for logging.

    Returns None in case of an error.
    """
    try:
        priv = priv_pem.encode("ascii")
        priv = load_pem_private_key(priv, password=None)
        return priv.public_key()

    except Exception as e:
        # Make sure we don't log the private key.
        typename = type(e).__name__
        logger.error("%s while generating public key for %d", typename, id)
        return None
