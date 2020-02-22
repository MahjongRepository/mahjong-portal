from django import forms

from account.models import User


class RequestPasswordReset(forms.Form):
    email = forms.EmailField()

    def clean(self):
        email = self.cleaned_data.get("email")
        if email:
            try:
                user = User.objects.get(email=email)
                self.cleaned_data["user"] = user
            except User.DoesNotExist:
                raise forms.ValidationError("User does't exists")
        return self.cleaned_data
