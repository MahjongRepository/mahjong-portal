from django.contrib import admin
from django import forms

from online.models import TournamentStatus, TournamentPlayers, TournamentGame, TournamentGamePlayer
from tournament.models import Tournament, OnlineTournamentRegistration


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

        self.fields['tournament'].queryset = Tournament.objects.filter(tournament_type=Tournament.ONLINE).order_by('-start_date')


class TournamentStatusAdmin(admin.ModelAdmin):
    list_display = ['tournament', 'current_round', 'end_break_time']


class TournamentPlayersAdmin(admin.ModelAdmin):
    form = TournamentPlayersForm
    list_display = ['tournament', 'player', 'telegram_username', 'tenhou_username', 'pantheon_id']
    list_filter = [
        ['tournament', admin.RelatedOnlyFieldListFilter],
    ]

    def player(self, obj):
        try:
            registration = OnlineTournamentRegistration.objects.filter(tenhou_nickname=obj.tenhou_username).last()
            return registration.player
        except:
            result = OnlineTournamentRegistration.objects.filter(tenhou_nickname=obj.tenhou_username).last()
            if result:
                return u'[{} {}]'.format(result.last_name, result.first_name)

        return None


class TournamentGameAdmin(admin.ModelAdmin):
    form = TournamentGameForm
    list_display = ['tournament', 'tournament_round', 'status', 'log_id', 'created_on', 'updated_on']
    list_filter = [['tournament', admin.RelatedOnlyFieldListFilter], 'status', 'tournament_round',]


class TournamentGamePlayerAdmin(admin.ModelAdmin):
    list_display = ['player', 'game', 'wind', 'is_active']
    list_filter = [['game__tournament', admin.RelatedOnlyFieldListFilter], 'game__status']


admin.site.register(TournamentStatus, TournamentStatusAdmin)
admin.site.register(TournamentPlayers, TournamentPlayersAdmin)
admin.site.register(TournamentGame, TournamentGameAdmin)
admin.site.register(TournamentGamePlayer, TournamentGamePlayerAdmin)
