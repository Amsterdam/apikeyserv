from http import HTTPStatus
import json
import logging
from typing import Optional

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from .display import jwks
from .forms import RequestForm
from .models import ApiKey, SigningKey, sign


logger = logging.getLogger(__file__)


def index(request):
    """Renders all active signing keys as a JWKS."""
    active_keys = SigningKey.objects.filter(active=True)

    keyset = []

    for priv, id in active_keys.values_list("private", "id"):
        pub = public_key(priv, id)
        if pub is None:
            continue

        keyset.append(pub)

    j = json.dumps(jwks(keyset))
    return HttpResponse(j, content_type="application/json")


@csrf_exempt
def api_keys(request):
    """API endpoint for requesting new api keys."""
    if request.method == "OPTIONS":
        return HttpResponse(status=204)
    if request.method == "GET":
        # We do not want to expose the keys
        raise PermissionDenied()
    elif request.method == "POST":
        # do validations and add a key
        if not request.body:
            return JsonResponse({"message": "No data provided."}, status=HTTPStatus.BAD_REQUEST)
        params = json.loads(request.body)
        try:
            form = RequestForm(params)
            if not form.is_valid():
                return JsonResponse(form.errors, status=HTTPStatus.BAD_REQUEST)
            del params["agree_on_personal_data"]
            new_key = ApiKey(**params)
        except TypeError:
            return JsonResponse({"message": "Invalid parameters."}, status=HTTPStatus.BAD_REQUEST)
        new_key.save()
        logger.info(
            "Key created for %s, %s", params.get("organisation", ""), params.get("email_1")
        )
        return JsonResponse(new_key.as_json())


def public_key(priv_pem: str, id: int) -> Optional[Ed25519PublicKey]:
    """Returns the public key for the private key priv_pem.

    The private key must be in PEM format.

    The id is the database id, used for logging.

    Returns None in case of an error.
    """
    try:
        priv = priv_pem.encode("ascii")
        priv = load_pem_private_key(priv, password=None)
        return priv.public_key()

    except Exception as e:
        # Make sure we don't log the private key.
        typename = type(e).__name__
        logger.error("%s while generating public key for %d", typename, id)
        return None


def _build_url_with_script_name(request, path):
    if (forced_script_name := settings.FORCE_SCRIPT_NAME) is not None:
        path = forced_script_name + path
    return request.build_absolute_uri(path)


def request_new_key(request):
    """Handle a (POST) request for a new API key."""
    if request.method == "POST":
        form = RequestForm(request.POST)
        logger.info("New key request")

        if form.is_valid():
            params = form.cleaned_data
            del params["agree_on_personal_data"]
            new_key = ApiKey(**params)
            new_key.save()
            data = form.cleaned_data
            logger.info("Key created for %s, %s", data["organisation"], data["email_1"])
            return render(request, "apikeys/created.html", {"apikey": sign(new_key)})
    else:
        form = RequestForm()

    docs_url = _build_url_with_script_name(request, "/docs/")
    return render(request, "apikeys/form.html", {"form": form, "docs_url": docs_url})


def documentation(request):
    form_url =_build_url_with_script_name(request, "/register/")
    return render(request, "apikeys/docs.html", {"form_url": form_url})
