from django import forms
from django.contrib import admin

from league.models import League, LeaguePlayer, LeagueTeam


class LeagueForm(forms.ModelForm):
    class Meta:
        model = League
        exclude = ["name", "description"]


class LeagueAdmin(admin.ModelAdmin):
    form = LeagueForm
    prepopulated_fields = {"slug": ["name_en"]}

    list_display = ["name", "start_date", "end_date"]


class LeagueTeamAdmin(admin.ModelAdmin):
    search_fields = [
        "name",
    ]
    list_display = ["name", "number", "league"]


class LeaguePlayerAdmin(admin.ModelAdmin):
    search_fields = ["name", "team__name"]
    list_display = ["name", "team"]


admin.site.register(League, LeagueAdmin)
admin.site.register(LeagueTeam, LeagueTeamAdmin)
admin.site.register(LeaguePlayer, LeaguePlayerAdmin)
