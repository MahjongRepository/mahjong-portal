from django.db import models
from django.urls import reverse

from club.models import Club
from mahjong_portal.models import BaseModel
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

    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField()

    number_of_sessions = models.PositiveSmallIntegerField(default=0, blank=True)
    number_of_players = models.PositiveSmallIntegerField(default=0, blank=True)
    game_type = models.PositiveSmallIntegerField(choices=GAME_TYPES, default=RIICHI)

    is_upcoming = models.BooleanField(default=False)
    registration_description = models.TextField(null=True, blank=True, default='')
    registration_link = models.URLField(null=True, blank=True, default='')

    clubs = models.ManyToManyField(Club, blank=True)
    country = models.ForeignKey(Country, on_delete=models.PROTECT)
    city = models.ForeignKey(City, on_delete=models.PROTECT, null=True, blank=True)
    tournament_type = models.ForeignKey(TournamentType, on_delete=models.PROTECT)

    need_qualification = models.BooleanField(default=False)
    has_accreditation = models.BooleanField(default=True)

    pantheon_id = models.CharField(max_length=20, null=True, blank=True)

    ema_id = models.CharField(max_length=20, null=True, blank=True)

    def __unicode__(self):
        return self.name

    def is_official_ema(self):
        return self.tournament_type.slug != TournamentType.CLUB

    def get_url(self):
        if self.is_upcoming:
            return reverse('tournament_announcement', kwargs={'slug': self.slug})
        else:
            return reverse('tournament_details', kwargs={'slug': self.slug})


class TournamentResult(BaseModel):
    tournament = models.ForeignKey(Tournament, related_name='results', on_delete=models.PROTECT)
    player = models.ForeignKey(Player, on_delete=models.PROTECT, related_name='tournament_results')
    place = models.PositiveSmallIntegerField()
    scores = models.DecimalField(default=None, decimal_places=2, max_digits=10, null=True, blank=True)

    def __unicode__(self):
        return self.tournament.name
