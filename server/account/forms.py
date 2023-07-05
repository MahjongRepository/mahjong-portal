from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from sentry_sdk import capture_exception

from pantheon_api.api_calls.user import get_current_pantheon_user_data, login_through_pantheon


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

    user_data = None

    def clean(self):
        email = self.cleaned_data.get("email")
        password = self.cleaned_data.get("password")

        if email is not None and password:
            email = email.lower().strip()
            try:
                response = login_through_pantheon(email, password)
                self.user_data = get_current_pantheon_user_data(response.person_id)
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
