from django.db import models

from club.models import Club
from mahjong_portal.models import BaseModel
from player.models import Player


class ClubSession(BaseModel):
    club = models.ForeignKey(Club, related_name='club_sessions')
    date = models.DateTimeField()

    pantheon_id = models.CharField(max_length=255, null=True, blank=True)


class ClubSessionResult(BaseModel):
    club_session = models.ForeignKey(ClubSession, related_name='results')
    player = models.ForeignKey(Player, null=True, blank=True)
    player_string = models.CharField(max_length=255, null=True, blank=True)

    order = models.PositiveSmallIntegerField()
    place = models.PositiveSmallIntegerField()
    score = models.IntegerField()

    class Meta:
        ordering = ['order']

    @property
    def wind(self):
        winds = [u'東', u'南', u'西', u'北']
        return winds[self.order - 1]


class ClubRating(BaseModel):
    club = models.ForeignKey(Club, related_name='rating')
    player = models.ForeignKey(Player, null=True, blank=True)
    player_string = models.CharField(max_length=255, null=True, blank=True)

    games_count = models.PositiveIntegerField()
    average_place = models.DecimalField(decimal_places=2, max_digits=10)
    ippatsu_chance = models.DecimalField(decimal_places=2, max_digits=10)
    average_dora_in_hand = models.DecimalField(decimal_places=2, max_digits=10)
