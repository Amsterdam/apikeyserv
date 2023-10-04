from datetime import datetime, timedelta
import jwt
import pytest

from apikeys.models import ApiKey, SigningKey, get_signing_key, sign


TEST_KEY = """-----BEGIN PRIVATE KEY-----
MC4CAQAwBQYDK2VwBCIEIOcQ07mLHkPVDRVrpB84Y/5BcrZok6dq8Ui4VMB2bgnS
-----END PRIVATE KEY-----"""


@pytest.mark.django_db
def test_apikey_sign():
    api_key = ApiKey.objects.create(id=1)
    SigningKey.objects.create(private=TEST_KEY).save()
    signing_key = get_signing_key()
    assert signing_key == TEST_KEY

    signed = sign(api_key)

    all_algs = set(jwt.algorithms.get_default_algorithms())
    for algs in [["EdDSA"], all_algs]:
        decoded = jwt.decode(signed, signing_key, algs)
        assert decoded["sub"] == api_key.id

    with pytest.raises(Exception):
        jwt.decode(signed, signing_key, algorithms=all_algs - {"EdDSA"})


@pytest.mark.django_db
def test_apikey_expiry():
    api_key = ApiKey.objects.create(id=1, expires=datetime.now() - timedelta(days=1))
    SigningKey.objects.create(private=TEST_KEY).save()
    signing_key = get_signing_key()
    signed = sign(api_key)
    with pytest.raises(jwt.ExpiredSignatureError):
        jwt.decode(signed, signing_key, algorithms="EdDSA")
