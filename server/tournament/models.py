from django.db import models
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

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

    registration_description = models.TextField(null=True, blank=True, default='')
    registration_link = models.URLField(null=True, blank=True, default='')

    clubs = models.ManyToManyField(Club, blank=True)
    country = models.ForeignKey(Country, on_delete=models.PROTECT)
    city = models.ForeignKey(City, on_delete=models.PROTECT, null=True, blank=True)
    tournament_type = models.ForeignKey(TournamentType, on_delete=models.PROTECT)

    is_upcoming = models.BooleanField(default=False)
    need_qualification = models.BooleanField(default=False)
    has_accreditation = models.BooleanField(default=True)
    opened_registration = models.BooleanField(default=False)

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

    @property
    def base_rank(self):
        number_of_players = self.tournament.number_of_players
        place = self.place

        # first place
        if place == 1:
            return 1000

        if place == number_of_players:
            return 0

        return round(((number_of_players - place) / (number_of_players - 1)) * 1000, 2)


class TournamentRegistration(BaseModel):
    tournament = models.ForeignKey(Tournament, related_name='tournament_registrations', on_delete=models.PROTECT)

    first_name = models.CharField(max_length=255, verbose_name=_('First name'))
    last_name = models.CharField(max_length=255, verbose_name=_('Last name'))
    city = models.CharField(max_length=255, verbose_name=_('City'))
    phone = models.CharField(max_length=255, verbose_name=_('Phone'),
                             help_text=_('It will be visible only to the tournament administrator'))

    player = models.ForeignKey(Player, null=True, blank=True, related_name='tournament_registrations')
    city_object = models.ForeignKey(City, null=True, blank=True)

    def __unicode__(self):
        return self.full_name

    @property
    def full_name(self):
        return u'{} {}'.format(self.last_name, self.first_name)
