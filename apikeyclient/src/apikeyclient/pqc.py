"""Optional ML-DSA-65 (FIPS 204) verification support for apikeyclient.

apikeyserv can sign API keys with ML-DSA-65 as well as its original EdDSA (see its
own apikeys/pqc.py) -- a second, opt-in algorithm, not a replacement. This module is
what lets apikeyclient verify those tokens too, but only if the optional 'pqc' extra
(liboqs-python) is installed: `pip install datadiensten-apikeyclient[pqc]`.

Without that extra, `AVAILABLE` is False and this client simply keeps verifying
EdDSA-signed keys exactly as it always has -- it just can't verify ML-DSA-65-signed
ones yet. This is deliberate: liboqs-python needs a C toolchain to build its
underlying library, which is a real cost not every consumer of this package should
be forced to pay just to keep doing what already works today.
"""

import base64

ALGORITHM = "ML-DSA-65"

try:
    import jwt
    import oqs
    from jwt.algorithms import Algorithm

    class MLDSA65Algorithm(Algorithm):
        """Verifies ML-DSA-65 signatures. apikeyclient only ever verifies, so
        signing isn't implemented here -- see apikeyserv's own apikeys/pqc.py for
        that half."""

        def prepare_key(self, key):
            if not isinstance(key, (bytes, bytearray)):
                raise TypeError("ML-DSA-65 keys must be raw bytes")
            return bytes(key)

        def sign(self, msg, key):
            raise NotImplementedError("apikeyclient only verifies ML-DSA-65 tokens, it doesn't sign them")

        def verify(self, msg: bytes, key: bytes, sig: bytes) -> bool:
            try:
                with oqs.Signature(ALGORITHM) as verifier:
                    return verifier.verify(msg, sig, key)
            except Exception:  # pragma: no cover
                # liboqs's own verify() already returns False (rather than raising)
                # for malformed key/signature bytes -- confirmed directly, this
                # branch isn't reachable with the current library version. Kept as
                # a defensive belt so this Algorithm's verify() contract (a plain
                # bool, never an exception) still holds if that ever changes.
                return False

        def to_jwk(self, key_obj, as_dict: bool = False):
            raise NotImplementedError("no standard ML-DSA-65 JWK shape to export")

        def from_jwk(self, jwk):
            raise NotImplementedError("use public_keys_from_jwks() instead")

    AVAILABLE = True
except ImportError:  # pragma: no cover
    # Exercised structurally, not by this test suite: this environment installs the
    # optional 'pqc' extra (see pyproject.toml) specifically so the tests above can
    # cover the "liboqs-python is installed" behavior. A consumer that hasn't
    # installed it takes this branch for real every time it imports apikeyclient --
    # see test_available_false_short_circuits_register_and_key_extraction below for
    # what AVAILABLE = False actually does downstream, which is what matters here.
    AVAILABLE = False


def register() -> None:
    """Registers the ML-DSA-65 algorithm with PyJWT if liboqs-python is installed.
    A no-op otherwise -- safe to call unconditionally at import time. Idempotent:
    PyJWT itself raises ValueError on a duplicate registration, which is exactly the
    already-registered case this swallows."""
    if not AVAILABLE:
        return
    try:
        jwt.register_algorithm(ALGORITHM, MLDSA65Algorithm())
    except ValueError:
        pass


def public_keys_from_jwks(keys: list) -> list:
    """Extracts raw ML-DSA-65 public key bytes from a JWKS 'keys' list.

    These entries use apikeyserv's own project-local JWK convention
    (`{"kty": "AKP", "alg": "ML-DSA-65", "pub": ...}`) -- there's no IETF-finalized
    JWK shape for ML-DSA yet, so PyJWT's own PyJWKSet/PyJWK can't and won't parse
    these (it skips any entry with an unrecognized "kty", which is exactly why
    an apikeyclient that hasn't installed the 'pqc' extra stays unaffected).

    Returns an empty list if liboqs-python isn't installed, since there'd be nothing
    that could verify these keys anyway.
    """
    if not AVAILABLE:
        return []

    result = []
    for entry in keys:
        if entry.get("alg") != ALGORITHM:
            continue
        pub = entry["pub"]
        padded = pub + "=" * (-len(pub) % 4)
        result.append(base64.urlsafe_b64decode(padded))
    return result
