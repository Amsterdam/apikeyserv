from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PublicKey,
    Ed25519PrivateKey,
)
import jwt

from .display import jwk, jwks


def test_jwk():
    # Example key from RFC 8037.
    pub = """d7 5a 98 01 82 b1 0a b7 d5 4b fe d3 c9 64 07 3a
             0e e1 72 f3 da a6 23 25 af 02 1a 68 f7 07 51 1a"""
    pub = bytes(int(part, base=16) for part in pub.split())
    pub = Ed25519PublicKey.from_public_bytes(pub)

    j = jwk(pub)
    assert j == {
        "kty": "OKP",
        "crv": "Ed25519",
        "x": "11qYAYKxCrfVS_7TyWQHOg7hcvPapiMlrwIaaPcHURo",
    }

    jwt.PyJWK(j)  # Shouldn't raise.


def test_jwks():
    keys = [Ed25519PrivateKey.generate().public_key() for i in range(5)]
    jwt.PyJWKSet(jwks(keys)["keys"])  # Shouldn't raise.
