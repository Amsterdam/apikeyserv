from cryptography.hazmat.primitives.serialization import (
    Encoding,
    PublicFormat,
    load_pem_private_key,
)
from django.http import HttpResponse
from io import StringIO
import logging
from typing import Optional

from .models import SigningKey


logger = logging.getLogger(__file__)


def index(request):
    # TODO: JWKS of all active signing keys.
    active_keys = SigningKey.objects.filter(active=True)

    output = StringIO()
    for priv, id in active_keys.values_list("private", "id"):
        pub = pem_public_key(priv, id)
        if pub is None:
            continue

        output.write(pub)
        output.write("\n")

    if (size := output.tell()) > 0:
        output.truncate(size - 1)  # Remove final newline.

    return HttpResponse(output.getvalue(), content_type="text/plain")


def pem_public_key(priv_pem: str, id: int) -> Optional[str]:
    """Returns the public key, in PEM format, for the private key priv_pem,
    also in PEM format.

    The id is the database id, used for logging.

    Returns None in case of an error.
    """
    try:
        priv_pem = priv_pem.encode("ascii")
        priv = load_pem_private_key(priv_pem, password=None)
        pub = priv.public_key()
        pub = pub.public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo)
        pub = pub.decode("ascii")
        return pub

    except Exception as e:
        # Make sure we don't log the private key.
        logger.error("%s while generating public key for %d", type(e).__name__, id)
        return None
