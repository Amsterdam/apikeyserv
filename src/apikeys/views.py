from django.http import HttpResponse
from django.shortcuts import render
import jwt

from .models import ApiKey
from signingkeys.models import get_signing_key


def index(request):
    return HttpResponse("Hello, world.")


def key_for_email(request, email):
    """Returns a signed API key (JWT) for the given email address."""

    sign_key = get_signing_key()

    try:
        token = ApiKey.objects.filter(email=email).values_list("key_id")[0][0]
    except IndexError:
        return HttpResponse("404")
    token = "%016x" % token

    return HttpResponse(jwt.encode({"sub": token}, sign_key),
                        content_type="text/plain")
