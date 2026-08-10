import pytest
from django.test import RequestFactory, override_settings
from django.urls import resolve

from apikeys.views import api_keys, documentation, index, request_new_key


def test_root_redirects_to_register(client):
    response = client.get("/", follow=False)

    assert response.status_code == 302
    assert response["Location"].endswith("register")


def test_apikey_routes_resolve_to_expected_views():
    assert resolve("/register/").func == request_new_key
    assert resolve("/docs/").func == documentation
    assert resolve("/apikeys/").func == api_keys
    assert resolve("/signingkeys/").func == index


def test_admin_route_is_available(client):
    response = client.get("/admin/", follow=False)

    assert response.status_code == 302
    assert "/admin/login/" in response["Location"]


@pytest.mark.django_db
def test_health_route_is_available(client):
    response = client.get("/status/health/")

    assert response.status_code == 200


@override_settings(FORCE_SCRIPT_NAME="/subpath")
def test_register_view_uses_forced_script_name_for_docs_link():
    request = RequestFactory().get("/register/")

    response = request_new_key(request)

    assert response.status_code == 200
    assert b'href="http://testserver/subpath/docs/"' in response.content


@override_settings(FORCE_SCRIPT_NAME="/subpath")
def test_documentation_view_uses_forced_script_name_for_form_link():
    request = RequestFactory().get("/docs/")

    response = documentation(request)

    assert response.status_code == 200
    assert b'href="http://testserver/subpath/register/"' in response.content