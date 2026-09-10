import jwt
import pytest
from django.core.management import call_command

from apikeys import pqc
from apikeys.models import SigningKey


TEST_KEY = """-----BEGIN PRIVATE KEY-----
MC4CAQAwBQYDK2VwBCIEIOcQ07mLHkPVDRVrpB84Y/5BcrZok6dq8Ui4VMB2bgnS
-----END PRIVATE KEY-----"""


@pytest.mark.django_db
def test_addsigningkey_command_creates_signing_key(tmp_path):
    pem_file = tmp_path / "signing-key.pem"
    pem_file.write_text(TEST_KEY)

    call_command("addsigningkey", str(pem_file))

    assert SigningKey.objects.count() == 1
    assert SigningKey.objects.get().private == TEST_KEY


@pytest.mark.django_db
def test_generatesigningkey_command_defaults_to_eddsa():
    call_command("generatesigningkey")

    key = SigningKey.objects.get()
    assert key.algorithm == "EdDSA"
    # Prove it's a real, usable EdDSA private key, not just any non-empty string.
    token = jwt.encode({"sub": "1"}, key.private, algorithm="EdDSA")
    assert jwt.decode(token, key.private, algorithms=["EdDSA"]) == {"sub": "1"}


@pytest.mark.django_db
def test_generatesigningkey_command_generates_mldsa65():
    call_command("generatesigningkey", "--algorithm", "ml-dsa-65")

    key = SigningKey.objects.get()
    assert key.algorithm == pqc.ALGORITHM
    secret_key, public_key = pqc.split_keys(key.private)
    token = jwt.encode({"sub": "1"}, secret_key, algorithm=pqc.ALGORITHM)
    assert jwt.decode(token, public_key, algorithms=[pqc.ALGORITHM]) == {"sub": "1"}


@pytest.mark.django_db
def test_generatesigningkey_command_rejects_unknown_algorithm():
    from django.core.management.base import CommandError

    with pytest.raises(CommandError):
        call_command("generatesigningkey", "--algorithm", "not-a-real-algorithm")

    assert SigningKey.objects.count() == 0