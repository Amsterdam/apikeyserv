from datetime import datetime, timedelta
import jwt
import pytest

from apikeys.models import ApiKey, SigningKey, get_signing_key, secure_random, sign


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
        assert decoded["sub"] == api_key.sub

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


@pytest.mark.django_db
def test_apikey_as_json_includes_signed_key_and_fields():
    SigningKey.objects.create(private=TEST_KEY).save()
    api_key = ApiKey.objects.create(
        id=123,
        organisation="Example Org",
        email_1="person@example.com",
    )

    payload = api_key.as_json()

    assert payload["id"] == 123
    assert payload["organisation"] == "Example Org"
    assert payload["email_1"] == "person@example.com"
    assert payload["apikey"]

    decoded = jwt.decode(payload["apikey"], TEST_KEY, algorithms=["EdDSA"])
    assert decoded["sub"] == api_key.sub


@pytest.mark.django_db
def test_sign_without_expiry_omits_exp_claim():
    SigningKey.objects.create(private=TEST_KEY).save()
    api_key = ApiKey.objects.create(id=456, expires=None)

    signed = sign(api_key)

    decoded = jwt.decode(signed, TEST_KEY, algorithms=["EdDSA"])
    assert decoded == {"sub": api_key.sub}


@pytest.mark.django_db
def test_get_signing_key_returns_newest_active_key():
    old_key = SigningKey.objects.create(private="old", active=True)
    newest_key = SigningKey.objects.create(private="newest", active=True)
    SigningKey.objects.create(private="inactive", active=False)

    old_created = datetime(2024, 1, 1, 12, 0, 0)
    new_created = datetime(2024, 1, 1, 12, 5, 0)
    SigningKey.objects.filter(pk=old_key.pk).update(created=old_created)
    SigningKey.objects.filter(pk=newest_key.pk).update(created=new_created)

    assert get_signing_key() == "newest"


def test_secure_random_returns_non_negative_63_bit_integer():
    value = secure_random()

    assert isinstance(value, int)
    assert 0 <= value < 2**63


@pytest.mark.django_db
def test_apikey_sub_is_stringified_primary_key():
    api_key = ApiKey.objects.create(id=789)

    assert api_key.sub == "789"
