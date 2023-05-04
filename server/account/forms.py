from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from sentry_sdk import capture_exception
from twirp.context import Context

from pantheon_api import frey_pb2
from pantheon_api.frey_twirp import FreyClient


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
            email = email.lower().strip()
            client = FreyClient(settings.PANTHEON_AUTH_API_URL)
            try:
                response = client.Authorize(
                    ctx=Context(),
                    request=frey_pb2.AuthAuthorizePayload(email=email, password=password),
                    server_path_prefix="/v2",
                )
                pantheon_id = response.personId
                auth_token = response.authToken

                response = client.Me(
                    ctx=Context(),
                    request=frey_pb2.AuthMePayload(person_id=pantheon_id, auth_token=auth_token),
                    server_path_prefix="/v2",
                )

                self.user_data = {
                    "id": pantheon_id,
                    "email": response.email,
                    "title": response.title,
                }
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
