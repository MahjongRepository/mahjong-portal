from django import forms
from django.utils.translation import ugettext_lazy as _

from tournament.models import TournamentRegistration, OnlineTournamentRegistration, TournamentApplication


class TournamentRegistrationForm(forms.ModelForm):
    allow_to_save_data = forms.BooleanField(required=True)

    class Meta:
        model = TournamentRegistration
        fields = ['last_name', 'first_name', 'city', 'phone', 'additional_contact', 'allow_to_save_data']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['allow_to_save_data'].label = _('I allow to store my personal data')


class OnlineTournamentRegistrationForm(forms.ModelForm):
    allow_to_save_data = forms.BooleanField(required=True)

    class Meta:
        model = OnlineTournamentRegistration
        fields = ['last_name', 'first_name', 'city', 'tenhou_nickname', 'contact', 'allow_to_save_data']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['allow_to_save_data'].label = _('I allow to store my personal data')


class TournamentApplicationForm(forms.ModelForm):
    allow_to_save_data = forms.BooleanField(required=True)

    class Meta:
        model = TournamentApplication
        exclude = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['allow_to_save_data'].label = _('I allow to store my personal data')
