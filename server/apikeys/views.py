import json
import logging
from typing import Optional

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.views.generic.base import TemplateView

from .display import jwks
from .forms import RequestForm
from .models import ApiKey, SigningKey


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


def api_keys(request):
    """ Stub for REST API, not sure if needed."""
    if request.method == "GET":
        # We do not want to expose the keys
        raise PermissionDenied()
    elif request.method == "POST":
        # do validations and add a key
        return JsonResponse({"status": "ok"})


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


def request_new_key(request):
    """Handle a (POST) request for a new API key."""
    if request.method == "POST":
        form = RequestForm(request.POST)
        logger.info("New key request")

        if form.is_valid():
            org = form.cleaned_data["organisation"]
            email = form.cleaned_data["email"]
            reason = form.cleaned_data["reason"]
            new_key = ApiKey(organisation=org, email=email, reason=reason)
            new_key.save()
            logger.info("Key created for %s, %s", org, email)
            return HttpResponseRedirect("/created/")
    else:
        form = RequestForm()

    return render(request, "apikeys/form.html", {"form": form})


class CreatedNewKey(TemplateView):
    template_name = "apikeys/created.html"
