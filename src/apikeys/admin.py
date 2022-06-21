from cryptography.hazmat.primitives.serialization import load_pem_private_key
from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError

from .display import base64_public_key
from .models import ApiKey, SigningKey, sign
from .views import public_key


class ApiKeyAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "created", "modified", "api_key")

    def api_key(self, obj):
        """API key with currently active signing key."""
        try:
            return sign(obj)
        except Exception:
            return ""

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
        """Displays the public key in base64, as JWK would."""
        try:
            key = public_key(obj.private, obj.id)
        except Exception:
            # Don't do anything that might log the private key.
            return "INVALID"

        return base64_public_key(key)


admin.site.register(ApiKey, ApiKeyAdmin)
admin.site.register(SigningKey, SigningKeyAdmin)
