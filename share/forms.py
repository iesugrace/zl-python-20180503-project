from django import forms


class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput())


class RenameForm(forms.Form):
    name = forms.CharField()


class ShareForm(forms.Form):
    code = forms.CharField(max_length=8, min_length=6, required=False)
    expire = forms.DateTimeField(required=False, disabled=True)
    anonymous = forms.BooleanField(required=False)
    never_expire = forms.BooleanField(required=False, initial=True)
