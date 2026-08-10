import pytest
from django.core.management import call_command

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