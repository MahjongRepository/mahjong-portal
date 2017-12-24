from django import forms
from django.contrib import admin

from tournament.models import Tournament


class TournamentForm(forms.ModelForm):

    class Meta:
        model = Tournament
        exclude = ['name']


class TournamentAdmin(admin.ModelAdmin):
    form = TournamentForm

    prepopulated_fields = {'slug': ['name_en']}
    list_display = ['name', 'date', 'is_enabled']

    ordering = ['-date']

    filter_horizontal = ['clubs']


admin.site.register(Tournament, TournamentAdmin)
