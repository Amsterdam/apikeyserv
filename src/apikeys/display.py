"""Key formatting for display to users and client applications."""

import base64

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from typing import Dict


def jwk(key: Ed25519PublicKey) -> Dict[str, object]:
    """Formats key in the JWK format (RFC 7517, RFC 8037)."""

    return {
        "kty": "OKP",
        "crv": "Ed25519",
        "x": base64_public_key(key),
    }


def base64_public_key(key: Ed25519PublicKey):
    raw = key.public_bytes(Encoding.Raw, PublicFormat.Raw)
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")
