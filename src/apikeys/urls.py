from django.urls import path

from . import views


urlpatterns = [
    #path("", views.index, name="index"),
    path("<email>/", views.key_for_email),
]
