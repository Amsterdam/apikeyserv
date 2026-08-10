import pytest
from django.contrib import admin
from django.test import RequestFactory

from apikeys.admin import ApiKeyAdmin, SigningKeyAdmin
from apikeys.display import base64_public_key
from apikeys.models import ApiKey, SigningKey
from apikeys.views import public_key


TEST_KEY = """-----BEGIN PRIVATE KEY-----
MC4CAQAwBQYDK2VwBCIEIOcQ07mLHkPVDRVrpB84Y/5BcrZok6dq8Ui4VMB2bgnS
-----END PRIVATE KEY-----"""


def admin_request():
    return RequestFactory().get("/admin/")


@pytest.mark.django_db
def test_signing_key_admin_form_accepts_valid_pem():
    admin_instance = SigningKeyAdmin(SigningKey, admin.site)
    form_class = admin_instance.get_form(admin_request())
    form = form_class(data={"private": TEST_KEY, "active": True})

    assert form.is_valid()


@pytest.mark.django_db
def test_signing_key_admin_form_rejects_invalid_pem():
    admin_instance = SigningKeyAdmin(SigningKey, admin.site)
    form_class = admin_instance.get_form(admin_request())
    form = form_class(data={"private": "invalid pem", "active": True})

    assert not form.is_valid()
    assert "private" in form.errors


def test_signing_key_admin_public_key_returns_base64_for_valid_key():
    admin_instance = SigningKeyAdmin(SigningKey, admin.site)
    signing_key = SigningKey(id=1, private=TEST_KEY)
    expected = base64_public_key(public_key(TEST_KEY, 1))

    assert admin_instance.public_key(signing_key) == expected


def test_signing_key_admin_public_key_returns_invalid_for_bad_data():
    admin_instance = SigningKeyAdmin(SigningKey, admin.site)
    signing_key = SigningKey(id=2, private="invalid pem")

    assert admin_instance.public_key(signing_key) == "INVALID"


@pytest.mark.django_db
def test_api_key_admin_api_key_returns_empty_string_when_signing_fails():
    admin_instance = ApiKeyAdmin(ApiKey, admin.site)
    api_key = ApiKey(id=123, organisation="Example Org", email_1="person@example.com")

    assert admin_instance.api_key(api_key) == ""