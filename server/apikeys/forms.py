from django import forms

from apikeys.models import ApiKey


class RequestForm(forms.ModelForm):
    class Meta:
        model = ApiKey
        exclude = ["id", "created", "modified", "expires", "sent"]
