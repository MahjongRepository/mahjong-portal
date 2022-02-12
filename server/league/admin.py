from django import forms
from django.contrib import admin

from league.models import League, LeagueGame, LeagueGameSlot, LeaguePlayer, LeagueTeam


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
    search_fields = ["name", "team__name", "tenhou_nickname"]
    list_display = ["name", "tenhou_nickname", "team"]


class LeagueGameAdmin(admin.ModelAdmin):
    list_display = ["status", "session"]


class LeagueGameSlotAdmin(admin.ModelAdmin):
    search_fields = ["assigned_player__name"]
    list_display = ["game", "team", "assigned_player"]


admin.site.register(League, LeagueAdmin)
admin.site.register(LeagueTeam, LeagueTeamAdmin)
admin.site.register(LeaguePlayer, LeaguePlayerAdmin)
admin.site.register(LeagueGame, LeagueGameAdmin)
admin.site.register(LeagueGameSlot, LeagueGameSlotAdmin)
