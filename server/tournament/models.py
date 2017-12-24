from django.db import models

from club.models import Club
from leaderboard.models import BaseModel
from player.models import Player
from settings.models import TournamentType, City, Country


class Tournament(BaseModel):
    RIICHI = 0
    MCR = 1
    GAME_TYPES = [
        [RIICHI, 'Riichi'],
        [MCR, 'MCR']
    ]

    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, max_length=255)

    date = models.DateField()
    number_of_days = models.PositiveSmallIntegerField(default=0)
    number_of_sessions = models.PositiveSmallIntegerField(default=0)
    number_of_players = models.PositiveSmallIntegerField(default=0)
    game_type = models.PositiveSmallIntegerField(choices=GAME_TYPES, default=RIICHI)

    is_enabled = models.BooleanField(default=True)

    clubs = models.ManyToManyField(Club)
    country = models.ForeignKey(Country, on_delete=models.PROTECT)
    city = models.ForeignKey(City, on_delete=models.PROTECT, null=True, blank=True)
    tournament_type = models.ForeignKey(TournamentType, on_delete=models.PROTECT)

    def __unicode__(self):
        return self.name

    def is_official_ema(self):
        return self.tournament_type.slug == 'ema'


class TournamentResult(BaseModel):
    tournament = models.ForeignKey(Tournament, related_name='results', on_delete=models.PROTECT)
    player = models.ForeignKey(Player, on_delete=models.PROTECT, related_name='tournament_results')
    place = models.PositiveSmallIntegerField()
    scores = models.DecimalField(default=None, decimal_places=2, max_digits=10, null=True, blank=True)

    def __unicode__(self):
        return self.name
