# -*- coding: utf-8 -*-

from django import forms

from tournament.models import (
    MsOnlineTournamentRegistration,
    OnlineTournamentRegistration,
    Tournament,
    TournamentRegistration,
)


class UploadResultsForm(forms.Form):
    csv_file = forms.FileField()
    switch_names = forms.BooleanField(required=False)
    ema = forms.BooleanField(required=False)
    auto_placing = forms.BooleanField(required=False, initial=True)


class TournamentForm(forms.ModelForm):
    class Meta:
        model = Tournament
        fields = [
            "name_ru",
            "name_en",
            "slug",
            "start_date",
            "end_date",
            "registration_description_ru",
            "registration_description_en",
        ]


class TournamentRegistrationNotesForm(forms.ModelForm):
    class Meta:
        model = TournamentRegistration
        fields = [
            "notes",
        ]


class OnlineTournamentRegistrationNotesForm(forms.ModelForm):
    class Meta:
        model = OnlineTournamentRegistration
        fields = [
            "notes",
        ]


class MsOnlineTournamentRegistrationNotesForm(forms.ModelForm):
    class Meta:
        model = MsOnlineTournamentRegistration
        fields = [
            "notes",
        ]
