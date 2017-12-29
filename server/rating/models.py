from django.db import models

from mahjong_portal.models import BaseModel
from player.models import Player
from tournament.models import Tournament


class Rating(BaseModel):
    INNER = 0
    EMA = 1
    TYPES = [
        [INNER, 'Inner'],
        [EMA, 'EMA']
    ]

    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)

    type = models.PositiveSmallIntegerField(choices=TYPES)

    def __unicode__(self):
        return self.name


class RatingDelta(BaseModel):
    rating = models.ForeignKey(Rating, on_delete=models.PROTECT)
    player = models.ForeignKey(Player, on_delete=models.PROTECT, related_name='rating_delta')
    tournament = models.ForeignKey(Tournament, on_delete=models.PROTECT, related_name='rating_delta')
    delta = models.IntegerField()
    is_active = models.BooleanField(default=False)

    tournament_place = models.PositiveSmallIntegerField(default=0)

    def __unicode__(self):
        return self.tournament.name


class RatingResult(BaseModel):
    rating = models.ForeignKey(Rating, on_delete=models.PROTECT)
    player = models.ForeignKey(Player, on_delete=models.PROTECT, related_name='rating_results')

    score = models.IntegerField(default=None, null=True, blank=True)
    place = models.PositiveIntegerField(default=None, null=True, blank=True)

    def __unicode__(self):
        return self.rating.name

    def get_deltas(self):
        return RatingDelta.objects.filter(player=self.player, rating=self.rating).order_by('-tournament__end_date')
