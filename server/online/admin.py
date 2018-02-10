from django.contrib import admin
from django import forms

from online.models import TournamentStatus, TournamentPlayers, TournamentGame, TournamentGamePlayer
from tournament.models import Tournament


class TournamentGameForm(forms.ModelForm):

    class Meta:
        model = TournamentGame
        exclude = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['tournament'].queryset = Tournament.objects.filter(tournament_type=Tournament.ONLINE)


class TournamentPlayersForm(forms.ModelForm):

    class Meta:
        model = TournamentPlayers
        exclude = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['tournament'].queryset = Tournament.objects.filter(tournament_type=Tournament.ONLINE)


class TournamentStatusAdmin(admin.ModelAdmin):
    list_display = ['tournament', 'current_round', 'end_break_time']


class TournamentPlayersAdmin(admin.ModelAdmin):
    form = TournamentPlayersForm
    list_display = ['tournament', 'telegram_username', 'tenhou_username', 'pantheon_id']


class TournamentGameAdmin(admin.ModelAdmin):
    form = TournamentGameForm
    list_display = ['tournament', 'tournament_round', 'status', 'log_id']
    list_filter = ['status', 'tournament_round']


class TournamentGamePlayerAdmin(admin.ModelAdmin):
    list_display = ['player', 'game', 'wind', 'is_active']
    list_filter = ['game__status']


admin.site.register(TournamentStatus, TournamentStatusAdmin)
admin.site.register(TournamentPlayers, TournamentPlayersAdmin)
admin.site.register(TournamentGame, TournamentGameAdmin)
admin.site.register(TournamentGamePlayer, TournamentGamePlayerAdmin)
