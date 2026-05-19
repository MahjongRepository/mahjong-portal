# -*- coding: utf-8 -*-

from django import forms
from django.utils.translation import gettext_lazy as _

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
    name_ru = forms.CharField(max_length=255, label=_("Name [ru]"), localize=True)
    name_en = forms.CharField(max_length=255, label=_("Name [en]"), localize=True)
    slug = forms.SlugField(max_length=255, label=_("Slug"), localize=True)
    start_date = forms.DateField(label=_("Start date"), localize=True)
    end_date = forms.DateField(label=_("End date"), localize=True)
    number_of_players = forms.DecimalField(min_value=0, label=_("Number of players"), localize=True)
    registration_description_ru = forms.CharField(
        widget=forms.Textarea, required=False, label=_("Registration description [ru]"), localize=True
    )
    registration_description_en = forms.CharField(
        widget=forms.Textarea, required=False, label=_("Registration description [en]"), localize=True
    )

    class Meta:
        model = Tournament
        fields = [
            "name_ru",
            "name_en",
            "slug",
            "start_date",
            "end_date",
            "number_of_players",
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
