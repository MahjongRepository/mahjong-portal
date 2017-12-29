from django import forms
from django.contrib import admin

from tournament.models import Tournament


class TournamentForm(forms.ModelForm):

    class Meta:
        model = Tournament
        exclude = ['name', 'registration_description']


class TournamentAdmin(admin.ModelAdmin):
    form = TournamentForm

    prepopulated_fields = {'slug': ['name_en']}
    list_display = ['name', 'country', 'start_date', 'end_date', 'is_upcoming']
    list_filter = ['tournament_type']

    ordering = ['-end_date']

    filter_horizontal = ['clubs']


admin.site.register(Tournament, TournamentAdmin)
