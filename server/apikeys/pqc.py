"""ML-DSA-65 (FIPS 204) support for apikeyserv's signing keys.

Adds ML-DSA-65 as a second, opt-in signing algorithm alongside the existing EdDSA
one, selected per SigningKey via its `algorithm` field -- not a replacement. Existing
EdDSA keys and tokens are entirely unaffected.

ML-DSA-65 comes from liboqs (Open Quantum Safe), via the `oqs` package -- no custom
cryptographic primitive is implemented here, only:

* a PyJWT Algorithm adapter, so jwt.encode/jwt.decode can use it like any other alg;
* a PEM-like envelope for storing a raw liboqs key pair in SigningKey.private
  (mirroring how an EdDSA key is already stored there as a PEM string). liboqs has
  no way to re-derive a public key from a secret key alone, so both are stored
  together, secret key first then public key -- both are fixed-size for a given
  algorithm, so they can be split back apart by offset;
* a JWK-like representation for publishing the public key via /signingkeys/. No IETF
  RFC yet standardizes a JWK shape for ML-DSA (the relevant JOSE/COSE PQC work is
  still draft-stage) -- the "kty": "AKP" used here is a disclosed, project-local
  convention, not a claim of standards compliance.
"""

import base64

import oqs
from jwt.algorithms import Algorithm


ALGORITHM = "ML-DSA-65"
JWK_KTY = "AKP"

_PEM_TYPE = "ML-DSA-65 PRIVATE KEY"
_PEM_HEADER = f"-----BEGIN {_PEM_TYPE}-----"
_PEM_FOOTER = f"-----END {_PEM_TYPE}-----"
_PEM_LINE_LENGTH = 64

# Fixed sizes for ML-DSA-65 keys, used to split the concatenated secret+public key
# blob stored in a SigningKey's PEM envelope back into its two halves. Confirmed via
# oqs.Signature("ML-DSA-65") key generation, not guessed.
_SECRET_KEY_SIZE = 4032
_PUBLIC_KEY_SIZE = 1952


class InvalidKeyError(ValueError):
    """Raised when a PEM string isn't a valid ML-DSA-65 private key envelope."""


def generate_private_key_pem() -> str:
    """Generates a new ML-DSA-65 key pair and returns it PEM-wrapped (secret key
    followed by public key -- see module docstring for why both must be stored)."""
    with oqs.Signature(ALGORITHM) as signer:
        public_key = signer.generate_keypair()
        secret_key = signer.export_secret_key()
    return _wrap(secret_key + public_key)


def split_keys(pem: str) -> tuple[bytes, bytes]:
    """Returns (secret_key, public_key) from a PEM produced by generate_private_key_pem.

    Raises InvalidKeyError if pem isn't a validly-formed or correctly-sized envelope.
    """
    data = _unwrap(pem)
    want_size = _SECRET_KEY_SIZE + _PUBLIC_KEY_SIZE
    if len(data) != want_size:
        raise InvalidKeyError(f"invalid ML-DSA-65 key size: got {len(data)}, want {want_size}")
    return data[:_SECRET_KEY_SIZE], data[_SECRET_KEY_SIZE:]


def public_key_from_pem(pem: str) -> bytes:
    """Returns just the public key half from a PEM produced by generate_private_key_pem."""
    return split_keys(pem)[1]


def base64_public_key(public_key: bytes) -> str:
    """Formats a raw ML-DSA-65 public key in base64, mirroring display.base64_public_key's
    format for EdDSA (used for admin display, not the JWK 'pub' field encoding)."""
    return base64.urlsafe_b64encode(public_key).rstrip(b"=").decode("ascii")


def jwk(public_key: bytes) -> dict:
    """Formats an ML-DSA-65 public key in this project's own JWK-like shape."""
    return {
        "kty": JWK_KTY,
        "alg": ALGORITHM,
        "pub": base64_public_key(public_key),
    }


def _wrap(data: bytes) -> str:
    body = base64.b64encode(data).decode("ascii")
    lines = [body[i : i + _PEM_LINE_LENGTH] for i in range(0, len(body), _PEM_LINE_LENGTH)]
    return "\n".join([_PEM_HEADER, *lines, _PEM_FOOTER])


def _unwrap(pem: str) -> bytes:
    lines = [line.strip() for line in pem.strip().splitlines() if line.strip()]
    if len(lines) < 2 or lines[0] != _PEM_HEADER or lines[-1] != _PEM_FOOTER:
        raise InvalidKeyError("not an ML-DSA-65 private key")
    try:
        return base64.b64decode("".join(lines[1:-1]), validate=True)
    except (base64.binascii.Error, ValueError) as e:
        raise InvalidKeyError("not a valid ML-DSA-65 private key") from e


class MLDSA65Algorithm(Algorithm):
    """Adapts liboqs's ML-DSA-65 (FIPS 204) for use as a PyJWT signing algorithm.

    Keys are raw bytes: the secret key half (see split_keys) for signing, the public
    key half for verification. JWK (de)serialization isn't implemented here -- see
    jwk()/public_key_from_pem() instead, since there's no standard ML-DSA-65 JWK
    shape PyJWT's own machinery would understand anyway.
    """

    def prepare_key(self, key):
        if not isinstance(key, (bytes, bytearray)):
            raise TypeError("ML-DSA-65 keys must be raw bytes")
        return bytes(key)

    def sign(self, msg: bytes, key: bytes) -> bytes:
        with oqs.Signature(ALGORITHM, secret_key=key) as signer:
            return signer.sign(msg)

    def verify(self, msg: bytes, key: bytes, sig: bytes) -> bool:
        try:
            with oqs.Signature(ALGORITHM) as verifier:
                return verifier.verify(msg, sig, key)
        except Exception:  # pragma: no cover
            # liboqs's own verify() already returns False (rather than raising) for
            # malformed key/signature bytes -- confirmed directly, this branch isn't
            # reachable with the current library version. Kept as a defensive belt
            # so PyJWT's Algorithm.verify contract (a plain bool, never an
            # exception) still holds if that ever changes in a future liboqs
            # release, rather than propagating an unrelated exception up through
            # jwt.decode.
            return False

    def to_jwk(self, key_obj, as_dict: bool = False):
        raise NotImplementedError("use pqc.jwk() to publish an ML-DSA-65 public key")

    def from_jwk(self, jwk_dict):
        raise NotImplementedError("use pqc.public_key_from_pem() or the raw 'pub' JWK field")


def register() -> None:
    """Registers the ML-DSA-65 algorithm with PyJWT. Idempotent -- safe to call more
    than once (e.g. once from apps.py and again from a test's own setup): PyJWT
    itself raises ValueError on a duplicate registration, which is exactly the
    already-registered case this swallows."""
    import jwt

    try:
        jwt.register_algorithm(ALGORITHM, MLDSA65Algorithm())
    except ValueError:
        pass
