import base64
import json

import jwt
import oqs
import pytest

from apikeyclient import pqc


ALGORITHM = "ML-DSA-65"


def _generate_keypair():
    with oqs.Signature(ALGORITHM) as signer:
        public_key = signer.generate_keypair()
        secret_key = signer.export_secret_key()
    return secret_key, public_key


def _sign(secret_key: bytes, message: bytes) -> bytes:
    with oqs.Signature(ALGORITHM, secret_key=secret_key) as signer:
        return signer.sign(message)


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _encode_token(payload: dict, secret_key: bytes) -> str:
    """Builds a compact JWT signed with ML-DSA-65 directly via oqs, the way
    apikeyserv's own apikeys/pqc.py would -- not via jwt.encode, since
    apikeyclient's own MLDSA65Algorithm deliberately can't sign (it only verifies)."""
    header = {"alg": ALGORITHM, "typ": "JWT"}
    signing_input = f"{_b64url(json.dumps(header).encode())}.{_b64url(json.dumps(payload).encode())}"
    signature = _sign(secret_key, signing_input.encode("ascii"))
    return f"{signing_input}.{_b64url(signature)}"


def test_pqc_available_in_this_test_environment():
    # This test environment installs the optional 'pqc' extra; if it didn't,
    # AVAILABLE would be False and every other test in this file would need
    # skipping instead.
    assert pqc.AVAILABLE is True


def test_register_is_idempotent():
    pqc.register()
    pqc.register()

    assert isinstance(jwt.get_algorithm_by_name(pqc.ALGORITHM), pqc.MLDSA65Algorithm)


def test_algorithm_verify_accepts_valid_signature():
    pqc.register()
    secret_key, public_key = _generate_keypair()
    message = b"some jwt signing input"
    signature = _sign(secret_key, message)

    algorithm = pqc.MLDSA65Algorithm()
    assert algorithm.verify(message, public_key, signature) is True


def test_algorithm_verify_rejects_wrong_key():
    secret_key, _public_key = _generate_keypair()
    _other_secret_key, other_public_key = _generate_keypair()
    message = b"some jwt signing input"
    signature = _sign(secret_key, message)

    algorithm = pqc.MLDSA65Algorithm()
    assert algorithm.verify(message, other_public_key, signature) is False


def test_algorithm_verify_returns_false_on_garbage_input_instead_of_raising():
    algorithm = pqc.MLDSA65Algorithm()

    assert algorithm.verify(b"msg", b"not a real key", b"not a real signature") is False


def test_algorithm_prepare_key_rejects_non_bytes():
    algorithm = pqc.MLDSA65Algorithm()

    with pytest.raises(TypeError):
        algorithm.prepare_key("not bytes")


def test_algorithm_sign_not_implemented():
    algorithm = pqc.MLDSA65Algorithm()

    with pytest.raises(NotImplementedError):
        algorithm.sign(b"msg", b"key")


def test_algorithm_jwk_not_implemented():
    algorithm = pqc.MLDSA65Algorithm()

    with pytest.raises(NotImplementedError):
        algorithm.to_jwk(b"irrelevant")

    with pytest.raises(NotImplementedError):
        algorithm.from_jwk({})


def test_public_keys_from_jwks_extracts_matching_entries_only():
    _secret_key, public_key = _generate_keypair()
    encoded = base64.urlsafe_b64encode(public_key).rstrip(b"=").decode("ascii")

    keys = [
        {"kty": "OKP", "alg": "EdDSA", "crv": "Ed25519", "x": "irrelevant"},
        {"kty": "AKP", "alg": ALGORITHM, "pub": encoded},
    ]

    result = pqc.public_keys_from_jwks(keys)

    assert result == [public_key]


def test_public_keys_from_jwks_handles_unpadded_base64_of_any_length():
    # base64url without padding can be any length mod 4; make sure the manual
    # padding logic in public_keys_from_jwks handles all of them, not just the one
    # length the happy-path test above happens to produce.
    for payload in (b"a", b"ab", b"abc", b"abcd"):
        encoded = base64.urlsafe_b64encode(payload).rstrip(b"=").decode("ascii")
        keys = [{"kty": "AKP", "alg": ALGORITHM, "pub": encoded}]

        assert pqc.public_keys_from_jwks(keys) == [payload]


def test_public_keys_from_jwks_returns_empty_list_for_no_matches():
    keys = [{"kty": "OKP", "alg": "EdDSA", "crv": "Ed25519", "x": "irrelevant"}]

    assert pqc.public_keys_from_jwks(keys) == []


def test_end_to_end_check_token_verifies_mldsa65_signed_key():
    """Mirrors test_client.py's test_check_token, for the new algorithm: builds a
    token the way apikeyserv's own apikeys/pqc.py would sign one, and confirms
    apikeyclient's check_token (via the tagged-keys path) verifies it."""
    import apikeyclient

    secret_key, public_key = _generate_keypair()
    token = _encode_token({"sub": "999"}, secret_key)

    tagged_keys = [(public_key, [ALGORITHM])]
    assert apikeyclient.check_token(token, tagged_keys) == "999"


def test_available_false_short_circuits_register_and_key_extraction(monkeypatch):
    """Simulates a consumer that hasn't installed the optional 'pqc' extra: with
    AVAILABLE patched to False, register() and public_keys_from_jwks() must both
    become no-ops rather than touching `jwt`/`oqs` (which, for a real such consumer,
    wouldn't even be importable)."""
    monkeypatch.setattr(pqc, "AVAILABLE", False)

    pqc.register()  # must not raise even though jwt/oqs aren't referenced here

    keys = [{"kty": "AKP", "alg": ALGORITHM, "pub": "irrelevant"}]
    assert pqc.public_keys_from_jwks(keys) == []


def test_end_to_end_check_token_rejects_mldsa65_token_with_wrong_key():
    import apikeyclient

    secret_key, _public_key = _generate_keypair()
    _other_secret_key, other_public_key = _generate_keypair()
    token = _encode_token({"sub": "999"}, secret_key)

    tagged_keys = [(other_public_key, [ALGORITHM])]
    assert apikeyclient.check_token(token, tagged_keys) is None
