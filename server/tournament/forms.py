from django import forms

from tournament.models import TournamentRegistration, OnlineTournamentRegistration


class TournamentRegistrationForm(forms.ModelForm):

    class Meta:
        model = TournamentRegistration
        fields = ['last_name', 'first_name', 'city', 'phone', 'additional_contact']


class OnlineTournamentRegistrationForm(forms.ModelForm):

    class Meta:
        model = OnlineTournamentRegistration
        fields = ['last_name', 'first_name', 'city', 'tenhou_nickname', 'contact']
