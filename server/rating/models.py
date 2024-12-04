# -*- coding: utf-8 -*-

from django.db import models

from mahjong_portal.models import BaseModel
from player.models import Player
from tournament.models import Tournament
from utils.general import get_tournament_coefficient


class ExternalRating(BaseModel):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField(null=True, blank=True, default="")
    order = models.PositiveIntegerField(default=0)
    is_hidden = models.BooleanField(default=True)

    class Meta:
        ordering = ["id"]

    def __unicode__(self):
        return self.name


class ExternalRatingTournament(BaseModel):
    rating = models.ForeignKey(ExternalRating, on_delete=models.CASCADE)
    tournament = models.ForeignKey(Tournament, on_delete=models.PROTECT, related_name="external_rating_delta")

    def __unicode__(self):
        return self.tournament.name


class ExternalRatingDelta(BaseModel):
    rating = models.ForeignKey(ExternalRating, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.PROTECT, related_name="external_rating_delta")
    is_active = models.BooleanField(default=False)
    date = models.DateField(default=None, null=True, blank=True, db_index=True)
    base_rank = models.FloatField(default=0.0)
    place = models.PositiveIntegerField(default=None, null=True, blank=True)

    def __unicode__(self):
        return self.player.full_name


class ExternalRatingDate(BaseModel):
    rating = models.ForeignKey(ExternalRating, on_delete=models.CASCADE)
    date = models.DateField(db_index=True)

    class Meta:
        ordering = ["-date"]

    def __unicode__(self):
        return self.rating.__unicode__()


class Rating(BaseModel):
    RR = 0
    EMA = 1
    CRR = 2
    ONLINE = 3

    TYPES = [[RR, "RR"], [CRR, "CRR"], [EMA, "EMA"], [ONLINE, "ONLINE"]]

    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField(null=True, blank=True, default="")
    order = models.PositiveIntegerField(default=0)

    type = models.PositiveSmallIntegerField(choices=TYPES)

    class Meta:
        ordering = ["id"]

    def __unicode__(self):
        return self.name

    def is_online(self):
        return self.type == self.ONLINE


class RatingDelta(BaseModel):
    rating = models.ForeignKey(Rating, on_delete=models.PROTECT)
    player = models.ForeignKey(Player, on_delete=models.PROTECT, related_name="rating_delta")
    tournament = models.ForeignKey(Tournament, on_delete=models.PROTECT, related_name="rating_delta")
    is_active = models.BooleanField(default=False)

    base_rank = models.DecimalField(decimal_places=2, max_digits=10)
    delta = models.DecimalField(decimal_places=2, max_digits=10)
    date = models.DateField(default=None, null=True, blank=True, db_index=True)

    tournament_place = models.PositiveSmallIntegerField(default=0)

    def __unicode__(self):
        return self.tournament.name

    @property
    def coefficient_obj(self):
        return TournamentCoefficients.objects.get(rating=self.rating, tournament=self.tournament, date=self.date)

    @property
    def coefficient_value(self):
        coefficient_obj = self.coefficient_obj
        return get_tournament_coefficient(
            self.rating.type == Rating.EMA, self.tournament_id, self.player, coefficient_obj.coefficient
        )


class RatingResult(BaseModel):
    rating = models.ForeignKey(Rating, on_delete=models.PROTECT)
    player = models.ForeignKey(Player, on_delete=models.PROTECT, related_name="rating_results")

    score = models.DecimalField(default=None, decimal_places=2, max_digits=10, null=True, blank=True)
    place = models.PositiveIntegerField(default=None, null=True, blank=True)
    date = models.DateField(default=None, null=True, blank=True, db_index=True)
    tournament_numbers = models.PositiveIntegerField(null=True, blank=True)

    rating_calculation = models.TextField(null=True, blank=True)

    def __unicode__(self):
        return self.rating.name

    def get_deltas(self):
        return (
            RatingDelta.objects.filter(player=self.player, rating=self.rating)
            .filter(is_active=True)
            .prefetch_related("player")
            .prefetch_related("tournament")
            .order_by("-tournament__end_date")
        )


class TournamentCoefficients(BaseModel):
    rating = models.ForeignKey(Rating, on_delete=models.CASCADE)
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name="rating_results")
    date = models.DateField(default=None, null=True, blank=True, db_index=True)

    coefficient = models.DecimalField(decimal_places=2, max_digits=10, null=True, blank=True)
    age = models.DecimalField(decimal_places=2, max_digits=10, null=True, blank=True)
    previous_age = models.DecimalField(decimal_places=2, max_digits=10, null=True, blank=True)

    def __unicode__(self):
        return self.rating.name


class RatingDate(BaseModel):
    rating = models.ForeignKey(Rating, on_delete=models.CASCADE)
    date = models.DateField(db_index=True)
    is_future = models.BooleanField(default=False)

    class Meta:
        ordering = ["-date"]

    def __unicode__(self):
        return self.rating.__unicode__()
