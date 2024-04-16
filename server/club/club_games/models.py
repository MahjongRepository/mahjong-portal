# -*- coding: utf-8 -*-

from django.db import models

from club.models import Club
from mahjong_portal.models import BaseModel
from player.models import Player
from player.tenhou.models import TenhouAggregatedStatistics


# Disable club rating for now, since we are not syncing data with new pantheon yet
class EmptyResponseManager(models.Manager):
    def get_queryset(self):
        queryset = super(EmptyResponseManager, self).get_queryset()
        return queryset.none()


class ClubSessionSyncData(BaseModel):
    objects = EmptyResponseManager()

    club = models.OneToOneField(Club, on_delete=models.CASCADE, related_name="sync_info")
    last_session_id = models.PositiveIntegerField(null=True, blank=True)


class ClubSession(BaseModel):
    objects = EmptyResponseManager()

    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name="club_sessions")
    date = models.DateTimeField()

    pantheon_id = models.CharField(max_length=255, null=True, blank=True)
    pantheon_event_id = models.PositiveIntegerField(null=True, blank=True)

    def __unicode__(self):
        return self.date


class ClubSessionResult(BaseModel):
    objects = EmptyResponseManager()

    club_session = models.ForeignKey(ClubSession, on_delete=models.CASCADE, related_name="results")
    player = models.ForeignKey(Player, on_delete=models.CASCADE, null=True, blank=True)
    player_string = models.CharField(max_length=255, null=True, blank=True)

    order = models.PositiveSmallIntegerField()
    place = models.PositiveSmallIntegerField()
    score = models.IntegerField()

    class Meta:
        ordering = ["order"]

    @property
    def wind(self):
        winds = ["東", "南", "西", "北"]
        return winds[self.order - 1]


class ClubRating(BaseModel):
    objects = EmptyResponseManager()

    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name="rating")
    player = models.ForeignKey(Player, on_delete=models.CASCADE, null=True, blank=True)
    player_string = models.CharField(max_length=255, null=True, blank=True)

    games_count = models.PositiveIntegerField()
    average_place = models.DecimalField(decimal_places=2, max_digits=10)
    first_place = models.DecimalField(decimal_places=2, max_digits=10)
    second_place = models.DecimalField(decimal_places=2, max_digits=10)
    third_place = models.DecimalField(decimal_places=2, max_digits=10)
    fourth_place = models.DecimalField(decimal_places=2, max_digits=10)

    rank = models.PositiveSmallIntegerField(
        choices=TenhouAggregatedStatistics.RANKS, null=True, blank=True, default=None
    )
