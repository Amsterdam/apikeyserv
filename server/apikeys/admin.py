from cryptography.hazmat.primitives.serialization import load_pem_private_key
from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError

from . import pqc
from .display import base64_public_key
from .models import ApiKey, SigningKey, sign
from .views import public_key


class ApiKeyAdmin(admin.ModelAdmin):
    list_display = ("id", "email_1", "created", "modified", "api_key")

    def api_key(self, obj):
        """API key with currently active signing key."""
        try:
            return sign(obj)
        except Exception:
            return ""

class SigningKeyAdminForm(forms.ModelForm):
    def clean(self):
        cleaned_data = super().clean()
        priv_pem = cleaned_data.get("private")
        algorithm = cleaned_data.get("algorithm")
        if priv_pem is None or algorithm is None:
            return cleaned_data

        try:
            if algorithm == pqc.ALGORITHM:
                pqc.split_keys(priv_pem)
            else:
                load_pem_private_key(priv_pem.encode("ascii"), password=None)
        except Exception as e:
            self.add_error("private", ValidationError(e))

        return cleaned_data


class SigningKeyAdmin(admin.ModelAdmin):
    form = SigningKeyAdminForm
    list_display = ("id", "algorithm", "active", "created", "public_key")

    def public_key(self, obj):
        """Displays the public key in base64, as JWK would."""
        try:
            if obj.algorithm == pqc.ALGORITHM:
                return pqc.base64_public_key(pqc.public_key_from_pem(obj.private))
            key = public_key(obj.private, obj.id)
        except Exception:
            # Don't do anything that might log the private key.
            return "INVALID"

        if key is None:
            return "INVALID"

        return base64_public_key(key)


admin.site.register(ApiKey, ApiKeyAdmin)
admin.site.register(SigningKey, SigningKeyAdmin)
