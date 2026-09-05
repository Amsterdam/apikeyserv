from django.apps import AppConfig


class ApikeysConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apikeys"

    def ready(self):
        from . import pqc

        pqc.register()
