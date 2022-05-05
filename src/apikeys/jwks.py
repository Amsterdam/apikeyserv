import base64

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from typing import Dict, Union


def jwk(key: Ed25519PublicKey) -> Dict[str, object]:
    """Formats key in the JWK format (RFC 7517, RFC 8037)."""

    raw = key.public_bytes(Encoding.Raw, PublicFormat.Raw)

    return {
        "kty": "OKP",
        "crv": "Ed25519",
        "x": base64.urlsafe_b64encode(raw).decode("ascii"),
    }
