from django.db import models

from mahjong_portal.models import BaseModel
from player.models import Player
from tournament.models import Tournament
from utils.general import get_tournament_coefficient


class Rating(BaseModel):
    RR = 0
    EMA = 1
    CRR = 2
    ONLINE = 3

    TYPES = [
        [RR, 'RR'],
        [CRR, 'CRR'],
        [EMA, 'EMA'],
        [ONLINE, 'ONLINE']
    ]

    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField(null=True, blank=True, default='')
    order = models.PositiveIntegerField(default=0)

    type = models.PositiveSmallIntegerField(choices=TYPES)

    class Meta:
        ordering = ['id']

    def __unicode__(self):
        return self.name

    def is_online(self):
        return self.type == self.ONLINE


class RatingDelta(BaseModel):
    rating = models.ForeignKey(Rating, on_delete=models.PROTECT)
    player = models.ForeignKey(Player, on_delete=models.PROTECT, related_name='rating_delta')
    tournament = models.ForeignKey(Tournament, on_delete=models.PROTECT, related_name='rating_delta')
    is_active = models.BooleanField(default=False)
    is_last = models.BooleanField(default=False)

    base_rank = models.DecimalField(decimal_places=2, max_digits=10)
    delta = models.DecimalField(decimal_places=2, max_digits=10)
    date = models.DateField(default=None, null=True, blank=True, db_index=True)

    tournament_place = models.PositiveSmallIntegerField(default=0)

    def __unicode__(self):
        return self.tournament.name

    @property
    def coefficient_obj(self):
        return (TournamentCoefficients.objects
                .filter(rating=self.rating, tournament=self.tournament)
                .order_by('-date')
                .last())

    @property
    def coefficient_value(self):
        coefficient_obj = self.coefficient_obj
        return get_tournament_coefficient(self.tournament_id, self.player, coefficient_obj.coefficient)


class RatingResult(BaseModel):
    rating = models.ForeignKey(Rating, on_delete=models.PROTECT)
    player = models.ForeignKey(Player, on_delete=models.PROTECT, related_name='rating_results')

    score = models.DecimalField(default=None, decimal_places=2, max_digits=10, null=True, blank=True)
    place = models.PositiveIntegerField(default=None, null=True, blank=True)
    date = models.DateField(default=None, null=True, blank=True, db_index=True)
    is_last = models.BooleanField(default=False, db_index=True)

    rating_calculation = models.TextField(null=True, blank=True)

    def __unicode__(self):
        return self.rating.name

    def get_deltas(self):
        return (RatingDelta.objects
                           .filter(player=self.player, rating=self.rating)
                           .filter(is_active=True)
                           .prefetch_related('player')
                           .prefetch_related('tournament')
                           .order_by('-tournament__end_date'))


class TournamentCoefficients(BaseModel):
    rating = models.ForeignKey(Rating, on_delete=models.CASCADE)
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='rating_results')
    date = models.DateField(default=None, null=True, blank=True, db_index=True)

    coefficient = models.DecimalField(decimal_places=2, max_digits=10, null=True, blank=True)
    age = models.DecimalField(decimal_places=2, max_digits=10, null=True, blank=True)

    def __unicode__(self):
        return self.rating.name
