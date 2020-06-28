from django import forms
from django.utils.translation import ugettext_lazy as _

from tournament.models import OnlineTournamentRegistration, TournamentApplication, TournamentRegistration


class TournamentRegistrationForm(forms.ModelForm):
    allow_to_save_data = forms.BooleanField(required=True)

    class Meta:
        model = TournamentRegistration
        fields = ["last_name", "first_name", "city", "phone", "additional_contact", "notes", "allow_to_save_data"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        tournament = kwargs.get("initial", {}).get("tournament")

        self.fields["allow_to_save_data"].label = _("I allow to store my personal data")
        if tournament.display_notes:
            self.fields["notes"].widget = forms.Textarea(attrs={"rows": 2})
        else:
            del self.fields["notes"]


class OnlineTournamentRegistrationForm(forms.ModelForm):
    allow_to_save_data = forms.BooleanField(required=True)

    class Meta:
        model = OnlineTournamentRegistration
        fields = ["last_name", "first_name", "city", "tenhou_nickname", "contact", "notes", "allow_to_save_data"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        tournament = kwargs.get("initial", {}).get("tournament")

        self.fields["allow_to_save_data"].label = _("I allow to store my personal data")

        if tournament.display_notes:
            self.fields["notes"].widget = forms.Textarea(attrs={"rows": 2})
        else:
            del self.fields["notes"]


class TournamentApplicationForm(forms.ModelForm):
    allow_to_save_data = forms.BooleanField(required=True)

    class Meta:
        model = TournamentApplication
        exclude = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["allow_to_save_data"].label = _("I allow to store my personal data")
