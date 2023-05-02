from django import forms


class RequestForm(forms.Form):
    name = forms.CharField(max_length=256)
    email = forms.CharField(max_length=256)
