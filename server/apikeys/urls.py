from django.urls import path

from . import views


urlpatterns = [
    path("", views.request_new_key),
    path("signingkeys/", views.index, name="index"),
    path("apikeys/", views.api_keys),
]
