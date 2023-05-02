from django.urls import path

from . import views


urlpatterns = [
    path("", views.request_new_key),
    path("created/", views.CreatedNewKey.as_view()),
    path("signingkeys/", views.index, name="index"),
]
