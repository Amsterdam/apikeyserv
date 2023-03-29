from django.urls import path

from . import views


urlpatterns = [
    path("signingkeys/", views.index, name="index"),
]
