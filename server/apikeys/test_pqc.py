import jwt
import pytest

from apikeys import pqc


def test_generate_private_key_pem_round_trips_through_split_keys():
    private_pem = pqc.generate_private_key_pem()

    assert private_pem.startswith("-----BEGIN ML-DSA-65 PRIVATE KEY-----")
    assert private_pem.endswith("-----END ML-DSA-65 PRIVATE KEY-----")

    secret_key, public_key = pqc.split_keys(private_pem)
    assert len(secret_key) == pqc._SECRET_KEY_SIZE
    assert len(public_key) == pqc._PUBLIC_KEY_SIZE

    # Generating again must produce different key material.
    other_secret_key, other_public_key = pqc.split_keys(pqc.generate_private_key_pem())
    assert other_secret_key != secret_key
    assert other_public_key != public_key


def test_public_key_from_pem_matches_split_keys():
    private_pem = pqc.generate_private_key_pem()

    _secret_key, public_key = pqc.split_keys(private_pem)

    assert pqc.public_key_from_pem(private_pem) == public_key


def test_split_keys_rejects_non_pem_string():
    with pytest.raises(pqc.InvalidKeyError):
        pqc.split_keys("not a pem at all")


def test_split_keys_rejects_wrong_size_payload():
    # Well-formed envelope, wrong amount of base64-decoded data inside it.
    bad_pem = "\n".join(
        ["-----BEGIN ML-DSA-65 PRIVATE KEY-----", "AAAA", "-----END ML-DSA-65 PRIVATE KEY-----"]
    )
    with pytest.raises(pqc.InvalidKeyError):
        pqc.split_keys(bad_pem)


def test_split_keys_rejects_invalid_base64_body():
    bad_pem = "\n".join(
        ["-----BEGIN ML-DSA-65 PRIVATE KEY-----", "not-valid-base64!!", "-----END ML-DSA-65 PRIVATE KEY-----"]
    )
    with pytest.raises(pqc.InvalidKeyError):
        pqc.split_keys(bad_pem)


def test_jwk_shape():
    private_pem = pqc.generate_private_key_pem()
    public_key = pqc.public_key_from_pem(private_pem)

    j = pqc.jwk(public_key)

    assert j["kty"] == pqc.JWK_KTY
    assert j["alg"] == pqc.ALGORITHM
    assert isinstance(j["pub"], str)
    assert "=" not in j["pub"]  # unpadded, matching the EdDSA JWK's own 'x' field


def test_register_is_idempotent():
    # Already registered once by apps.py's ready() when the app started; must not
    # raise when called again here (or a second time right after, for good measure).
    pqc.register()
    pqc.register()

    assert isinstance(jwt.get_algorithm_by_name(pqc.ALGORITHM), pqc.MLDSA65Algorithm)


def test_sign_and_verify_round_trip_via_jwt():
    pqc.register()
    private_pem = pqc.generate_private_key_pem()
    secret_key, public_key = pqc.split_keys(private_pem)

    token = jwt.encode({"sub": "1"}, secret_key, algorithm=pqc.ALGORITHM)
    decoded = jwt.decode(token, public_key, algorithms=[pqc.ALGORITHM])

    assert decoded == {"sub": "1"}


def test_tampered_signature_is_rejected():
    pqc.register()
    private_pem = pqc.generate_private_key_pem()
    secret_key, public_key = pqc.split_keys(private_pem)

    token = jwt.encode({"sub": "1"}, secret_key, algorithm=pqc.ALGORITHM)
    header, payload_b64, sig_b64 = token.split(".")
    flipped = ("A" if sig_b64[0] != "A" else "B") + sig_b64[1:]
    tampered = f"{header}.{payload_b64}.{flipped}"

    with pytest.raises(jwt.InvalidSignatureError):
        jwt.decode(tampered, public_key, algorithms=[pqc.ALGORITHM])


def test_wrong_public_key_is_rejected():
    pqc.register()
    secret_key, _public_key = pqc.split_keys(pqc.generate_private_key_pem())
    _other_secret_key, other_public_key = pqc.split_keys(pqc.generate_private_key_pem())

    token = jwt.encode({"sub": "1"}, secret_key, algorithm=pqc.ALGORITHM)

    with pytest.raises(jwt.InvalidSignatureError):
        jwt.decode(token, other_public_key, algorithms=[pqc.ALGORITHM])


def test_algorithm_prepare_key_rejects_non_bytes():
    algorithm = pqc.MLDSA65Algorithm()

    with pytest.raises(TypeError):
        algorithm.prepare_key("not bytes")


def test_algorithm_verify_returns_false_on_malformed_input_instead_of_raising():
    algorithm = pqc.MLDSA65Algorithm()

    assert algorithm.verify(b"msg", b"not a real public key", b"not a real signature") is False


def test_algorithm_to_jwk_and_from_jwk_not_implemented():
    algorithm = pqc.MLDSA65Algorithm()

    with pytest.raises(NotImplementedError):
        algorithm.to_jwk(b"irrelevant")

    with pytest.raises(NotImplementedError):
        algorithm.from_jwk({})
