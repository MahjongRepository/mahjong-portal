import requests
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from sentry_sdk import capture_exception

from utils.general import make_random_letters_and_digit_string


class LoginForm(forms.Form):
    """
    Base class for authenticating users. Extend this to get a form that accepts
    email/password logins.
    """

    next = forms.CharField(widget=forms.HiddenInput())
    email = forms.EmailField(label=_("Email"), widget=forms.TextInput(attrs={"autofocus": True}))
    password = forms.CharField(
        label=_("Password"),
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
        required=True,
    )

    error_messages = {
        "invalid_login": _("Please enter a correct email and password. Note that both fields may be case-sensitive."),
    }

    def clean(self):
        email = self.cleaned_data.get("email")
        password = self.cleaned_data.get("password")

        if email is not None and password:
            try:
                data = {
                    "jsonrpc": "2.0",
                    "method": "authorize",
                    "params": {"email": email, "password": password},
                    "id": make_random_letters_and_digit_string(),
                }

                headers = {"X-Auth-Token": settings.PANTHEON_ADMIN_TOKEN}
                response = requests.post(settings.PANTHEON_AUTH_API_URL, json=data, headers=headers)

                if response.json().get("error"):
                    raise self.get_invalid_login_error()

                pantheon_id, auth_token = response.json()["result"]

                data = {
                    "jsonrpc": "2.0",
                    "method": "me",
                    "params": {"id": pantheon_id, "clientSideToken": auth_token},
                    "id": make_random_letters_and_digit_string(),
                }

                headers = {"X-Auth-Token": settings.PANTHEON_ADMIN_TOKEN}
                response = requests.post(settings.PANTHEON_AUTH_API_URL, json=data, headers=headers)
                if response.json().get("error"):
                    raise self.get_invalid_login_error()

                assert response.json()["result"]["email"]
                self.user_data = response.json()["result"]
            except Exception as e:
                capture_exception(e)
                raise self.get_invalid_login_error() from None

        return self.cleaned_data

    def get_invalid_login_error(self):
        self.add_error("email", "")
        self.add_error("password", "")
        return ValidationError(
            self.error_messages["invalid_login"],
            code="invalid_login",
        )
