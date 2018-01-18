from django import forms
from django.contrib import admin

from tournament.models import Tournament, TournamentRegistration


class TournamentForm(forms.ModelForm):

    class Meta:
        model = Tournament
        exclude = ['name', 'registration_description']


class TournamentAdmin(admin.ModelAdmin):
    form = TournamentForm

    prepopulated_fields = {'slug': ['name_en']}
    list_display = ['name', 'country', 'end_date', 'is_upcoming']
    list_filter = ['tournament_type_new','need_qualification', 'country']
    search_fields = ['name_ru', 'name_en']

    ordering = ['-end_date']

    filter_horizontal = ['clubs']


class TournamentRegistrationAdmin(admin.ModelAdmin):
    list_display = ['id', 'is_approved', 'tournament', 'first_name', 'last_name', 'city', 'phone', 'player', 'city_object']

    raw_id_fields = ['tournament', 'player', 'city_object']


admin.site.register(Tournament, TournamentAdmin)
admin.site.register(TournamentRegistration, TournamentRegistrationAdmin)
