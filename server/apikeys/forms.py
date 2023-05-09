from django import forms


class RequestForm(forms.Form):
    organisation = forms.CharField(max_length=256)
    email = forms.CharField(max_length=256)
    reason = forms.CharField(max_length=512)
