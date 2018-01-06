from django.db import models

from mahjong_portal.models import BaseModel
from player.models import Player
from tournament.models import Tournament


class Rating(BaseModel):
    RR = 0
    EMA = 1
    CRR = 2

    TYPES = [
        [RR, 'RR'],
        [CRR, 'CRR'],
        [EMA, 'EMA']
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


class RatingDelta(BaseModel):
    rating = models.ForeignKey(Rating, on_delete=models.PROTECT)
    player = models.ForeignKey(Player, on_delete=models.PROTECT, related_name='rating_delta')
    tournament = models.ForeignKey(Tournament, on_delete=models.PROTECT, related_name='rating_delta')
    is_active = models.BooleanField(default=False)

    base_rank = models.DecimalField(decimal_places=2, max_digits=10)
    delta = models.DecimalField(decimal_places=2, max_digits=10)

    tournament_place = models.PositiveSmallIntegerField(default=0)

    def __unicode__(self):
        return self.tournament.name


class RatingResult(BaseModel):
    rating = models.ForeignKey(Rating, on_delete=models.PROTECT)
    player = models.ForeignKey(Player, on_delete=models.PROTECT, related_name='rating_results')

    score = models.DecimalField(default=None, decimal_places=2, max_digits=10, null=True, blank=True)
    place = models.PositiveIntegerField(default=None, null=True, blank=True)

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

    coefficient = models.DecimalField(decimal_places=2, max_digits=10, null=True, blank=True)
    age = models.DecimalField(decimal_places=2, max_digits=10, null=True, blank=True)

    def __unicode__(self):
        return self.rating.name
