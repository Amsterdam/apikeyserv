from django.contrib.admin.options import RedirectView
from django.urls import path

from . import views


urlpatterns = [
    path("", RedirectView.as_view(url="register", permanent=False)),
    path("register/", views.request_new_key),
    path("signingkeys/", views.index, name="index"),
    path("apikeys/", views.api_keys),
    path("docs.html", views.documentation),
]
