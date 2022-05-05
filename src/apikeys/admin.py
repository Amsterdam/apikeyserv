import jwt
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError

from .models import ApiKey, SigningKey, get_signing_key
from .views import public_key


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


class SigningKeyAdminForm(forms.ModelForm):
    def clean_private(self):
        priv_pem = self.cleaned_data["private"]
        try:
            load_pem_private_key(priv_pem.encode("ascii"), password=None)
        except Exception as e:
            raise ValidationError(e) from e
        return priv_pem


class SigningKeyAdmin(admin.ModelAdmin):
    form = SigningKeyAdminForm
    list_display = ("id", "active", "created", "public_key")

    def public_key(self, obj):
        try:
            pubkey = public_key(obj.private, obj.id)
        except Exception as e:
            return "INVALID"

        pubkey = pubkey.strip()
        pubkey = pubkey.lstrip("-----BEGIN PUBLIC KEY-----")
        pubkey = pubkey.rstrip("-----END PUBLIC KEY-----")
        return pubkey


admin.site.register(ApiKey, ApiKeyAdmin)
admin.site.register(SigningKey, SigningKeyAdmin)
