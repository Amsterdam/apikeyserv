#!/usr/bin/env python
import os
import sys
from django.conf import settings
from django.urls import re_path
from django.core.wsgi import get_wsgi_application
from django.http import HttpResponse

DEBUG = False

SECRET_KEY = "41+_$!j&y@zr#9cxdp6m9o3j&6dnk__bq*deii)5w6w744e7a#"

ALLOWED_HOSTS = ["*"]

APIKEY_ENDPOINT = os.getenv('APIKEY_ENDPOINT')
APIKEY_MANDATORY = int(os.getenv('APIKEY_MANDATORY', 0))
APIKEY_ALLOW_EMPTY = int(os.getenv('APIKEY_ALLOW_EMPTY', 0))

settings.configure(
    DEBUG=DEBUG,
    APIKEY_ENDPOINT=APIKEY_ENDPOINT,
    APIKEY_MANDATORY=APIKEY_MANDATORY,
    APIKEY_ALLOW_EMPTY=APIKEY_ALLOW_EMPTY,
    SECRET_KEY=SECRET_KEY,
    ALLOWED_HOSTS=ALLOWED_HOSTS,
    ROOT_URLCONF=__name__,
    MIDDLEWARE=(
        "django.middleware.common.CommonMiddleware",
        "django.middleware.csrf.CsrfViewMiddleware",
        "django.middleware.clickjacking.XFrameOptionsMiddleware",
        "apikeyclient.ApiKeyMiddleware",
    ),
)


def index(_request):
    return HttpResponse('{"status": "ok"}', content_type="application/json")


urlpatterns = (re_path(r"^$", index), re_path(r"^v1/wfs$", index))

application = get_wsgi_application()

if __name__ == "__main__":
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
