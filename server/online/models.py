from django.db import models

from mahjong_portal.models import BaseModel
from tournament.models import Tournament


class TournamentStatus(BaseModel):
    tournament = models.ForeignKey(Tournament)

    current_round = models.PositiveSmallIntegerField(null=True, blank=True)
    end_break_time = models.DateTimeField(null=True, blank=True)
    registration_closed = models.BooleanField(default=False)

    def __unicode__(self):
        return self.tournament.name


class TournamentPlayers(BaseModel):
    tournament = models.ForeignKey(Tournament)

    telegram_username = models.CharField(max_length=32)
    tenhou_username = models.CharField(max_length=8)

    pantheon_id = models.PositiveIntegerField(null=True, blank=True)
    added_to_pantheon = models.BooleanField(default=False)

    def __unicode__(self):
        return self.tenhou_username


class TournamentGame(BaseModel):
    NEW = 0
    STARTED = 1
    FAILED_TO_START = 2
    FINISHED = 3

    STATUSES = [
        [NEW, 'New'],
        [STARTED, 'Started'],
        [FAILED_TO_START, 'Failed to start'],
        [FINISHED, 'Finished'],
    ]

    tournament = models.ForeignKey(Tournament)
    tournament_round = models.PositiveSmallIntegerField(null=True, blank=True)
    log_id = models.CharField(max_length=32, null=True, blank=True)

    status = models.PositiveSmallIntegerField(choices=STATUSES, default=NEW)

    class Meta:
        ordering = ['-tournament', '-tournament_round', 'status', ]

    def __unicode__(self):
        return '{}, {}, {}'.format(self.id, self.get_status_display(), self.tournament_round)


class TournamentGamePlayer(BaseModel):
    player = models.ForeignKey(TournamentPlayers)
    game = models.ForeignKey(TournamentGame, related_name='game_players')

    wind = models.PositiveSmallIntegerField(null=True, blank=True, default=None)
    is_active = models.BooleanField(default=True)

    def __unicode__(self):
        return u'{}, {}'.format(self.player.__unicode__(), self.wind)
