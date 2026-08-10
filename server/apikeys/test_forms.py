import pytest

from apikeys.forms import RequestForm


def valid_payload(**overrides):
    payload = {
        "email_1": "person@example.com",
        "organisation": "Example Org",
        "agree_on_personal_data": True,
    }
    payload.update(overrides)
    return payload


def test_request_form_minimal_valid_payload_succeeds():
    form = RequestForm(data=valid_payload())

    assert form.is_valid()


def test_request_form_requires_agree_on_personal_data():
    payload = valid_payload()
    del payload["agree_on_personal_data"]

    form = RequestForm(data=payload)

    assert not form.is_valid()
    assert "agree_on_personal_data" in form.errors


def test_request_form_requires_email_1():
    payload = valid_payload()
    del payload["email_1"]

    form = RequestForm(data=payload)

    assert not form.is_valid()
    assert "email_1" in form.errors


def test_request_form_requires_organisation():
    payload = valid_payload()
    del payload["organisation"]

    form = RequestForm(data=payload)

    assert not form.is_valid()
    assert "organisation" in form.errors


@pytest.mark.django_db
def test_request_form_accepts_optional_secondary_contact_fields():
    form = RequestForm(
        data=valid_payload(
            contactperson_1_name="Primary Contact",
            contactperson_2_name="Secondary Contact",
            email_2="second@example.com",
            department="Data Services",
        )
    )

    assert form.is_valid()
    assert form.cleaned_data["contactperson_2_name"] == "Secondary Contact"
    assert form.cleaned_data["email_2"] == "second@example.com"
    assert form.cleaned_data["department"] == "Data Services"