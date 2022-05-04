import jwt
from django import forms
from django.contrib import admin

from .models import ApiKey
from signingkeys.models import get_signing_key


class ApiKeyAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "created", "modified", "api_key")

    def api_key(self, obj):
        """API key with currently active signing key."""
        try:
            sign_key = get_signing_key()
        except Exception as e:
            return ""

        payload = {"sub": obj.id}
        if obj.expires is not None:
            payload["exp"] = obj.expires
        return jwt.encode({"sub": obj.id}, sign_key)


admin.site.register(ApiKey, ApiKeyAdmin)
