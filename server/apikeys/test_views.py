import json
import logging

import jwt
import pytest
from django.test import RequestFactory

from apikeys.models import ApiKey, SigningKey
from apikeys.views import logger as views_logger, public_key, request_new_key


TEST_KEY = """-----BEGIN PRIVATE KEY-----
MC4CAQAwBQYDK2VwBCIEIOcQ07mLHkPVDRVrpB84Y/5BcrZok6dq8Ui4VMB2bgnS
-----END PRIVATE KEY-----"""

INVALID_KEY = "not a valid private key"


def create_signing_key(private=TEST_KEY, active=True):
    return SigningKey.objects.create(private=private, active=active)


def valid_payload(**overrides):
    payload = {
        "email_1": "person@example.com",
        "organisation": "Example Org",
        "agree_on_personal_data": True,
    }
    payload.update(overrides)
    return payload


@pytest.mark.django_db
def test_api_keys_post_valid_payload_returns_signed_key(client):
    create_signing_key()

    response = client.post(
        "/apikeys/",
        data=json.dumps(valid_payload()),
        content_type="application/json",
    )

    assert response.status_code == 200
    assert ApiKey.objects.count() == 1

    body = response.json()
    api_key = ApiKey.objects.get()
    assert body["organisation"] == "Example Org"
    assert body["email_1"] == "person@example.com"
    assert body["id"] == api_key.id
    assert "apikey" in body

    decoded = jwt.decode(body["apikey"], TEST_KEY, algorithms=["EdDSA"])
    assert decoded["sub"] == api_key.sub


@pytest.mark.django_db
def test_api_keys_options_returns_no_content(client):
    response = client.options("/apikeys/")

    assert response.status_code == 204


@pytest.mark.django_db
def test_api_keys_get_is_forbidden(client):
    response = client.get("/apikeys/")

    assert response.status_code == 403


@pytest.mark.django_db
def test_api_keys_post_empty_body_returns_bad_request(client):
    response = client.post("/apikeys/", data="", content_type="application/json")

    assert response.status_code == 400
    assert response.json() == {"message": "No data provided."}


@pytest.mark.django_db
def test_api_keys_post_invalid_form_returns_field_errors(client):
    create_signing_key()

    response = client.post(
        "/apikeys/",
        data=json.dumps({}),
        content_type="application/json",
    )

    assert response.status_code == 400
    body = response.json()
    assert "email_1" in body
    assert "organisation" in body
    assert "agree_on_personal_data" in body


@pytest.mark.django_db
def test_api_keys_post_unknown_fields_returns_invalid_parameters(client):
    create_signing_key()

    payload = valid_payload(unexpected_field="boom")
    response = client.post(
        "/apikeys/",
        data=json.dumps(payload),
        content_type="application/json",
    )

    assert response.status_code == 400
    assert response.json() == {"message": "Invalid parameters."}


@pytest.mark.django_db
def test_request_new_key_get_renders_form_with_docs_link():
    request = RequestFactory().get("/register/")

    response = request_new_key(request)

    assert response.status_code == 200
    assert b"Nieuwe sleutel aanvragen" in response.content
    assert b'href="http://testserver/docs/"' in response.content


@pytest.mark.django_db
def test_request_new_key_post_valid_payload_renders_created_page():
    create_signing_key()
    request = RequestFactory().post("/register/", data=valid_payload())

    response = request_new_key(request)

    assert response.status_code == 200
    assert ApiKey.objects.count() == 1
    assert b"Thank you for your request" in response.content

    api_key = ApiKey.objects.get()
    expected_token = jwt.encode({"sub": api_key.sub, "exp": api_key.expires}, TEST_KEY, algorithm="EdDSA")
    assert expected_token.encode("utf-8") in response.content


@pytest.mark.django_db
def test_request_new_key_post_invalid_payload_rerenders_form_with_errors():
    request = RequestFactory().post("/register/", data={})

    response = request_new_key(request)

    assert response.status_code == 200
    assert ApiKey.objects.count() == 0
    assert b"This field is required." in response.content


@pytest.mark.django_db
def test_signingkeys_returns_jwks_for_active_keys(client):
    create_signing_key()

    response = client.get("/signingkeys/")

    assert response.status_code == 200
    assert response["Content-Type"] == "application/json"
    body = response.json()
    assert set(body) == {"keys"}
    assert len(body["keys"]) == 1
    assert body["keys"][0]["kty"] == "OKP"
    assert body["keys"][0]["alg"] == "EdDSA"


@pytest.mark.django_db
def test_signingkeys_excludes_inactive_keys(client):
    create_signing_key(active=False)
    create_signing_key()

    response = client.get("/signingkeys/")

    assert response.status_code == 200
    assert len(response.json()["keys"]) == 1


@pytest.mark.django_db
def test_signingkeys_skips_invalid_pem(client):
    create_signing_key(private=INVALID_KEY)
    create_signing_key()

    response = client.get("/signingkeys/")

    assert response.status_code == 200
    assert len(response.json()["keys"]) == 1


def test_public_key_invalid_input_returns_none_and_logs_without_leaking_key(caplog):
    with caplog.at_level(logging.ERROR, logger=views_logger.name):
        result = public_key(INVALID_KEY, 99)

    assert result is None
    assert "while generating public key for 99" in caplog.text
    assert INVALID_KEY not in caplog.text