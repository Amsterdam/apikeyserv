from django import forms

from apikeys.models import ApiKey


class RequestForm(forms.ModelForm):
    agree_on_personal_data = forms.BooleanField(required = True)
    class Meta:
        model = ApiKey
        exclude = ["id", "created", "modified", "expires", "sent"]
