from django import forms

from tournament.models import TournamentRegistration


class TournamentRegistrationForm(forms.ModelForm):

    class Meta:
        model = TournamentRegistration
        fields = ['last_name', 'first_name', 'city', 'phone', 'additional_contact']
