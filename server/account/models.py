# -*- coding: utf-8 -*-

from django.contrib.auth.models import AbstractUser
from django.db import models

from mahjong_portal.models import BaseModel
from player.models import Player
from tournament.models import Tournament


class User(AbstractUser):
    is_tournament_manager = models.BooleanField(default=False)
    is_league_manager = models.BooleanField(default=False)
    is_ema_players_manager = models.BooleanField(default=False)
    managed_tournaments = models.ManyToManyField(Tournament, blank=True)
    new_pantheon_id = models.PositiveIntegerField(null=True, blank=True)

    attached_player = models.ForeignKey(Player, null=True, blank=True, on_delete=models.PROTECT)


class AttachingPlayerRequest(BaseModel):
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    player = models.ForeignKey(Player, on_delete=models.PROTECT, related_name="attaching_request")
    is_processed = models.BooleanField(default=False)
    contacts = models.TextField()

    def __unicode__(self):
        return self.player.__unicode__()


class PantheonInfoUpdateLog(BaseModel):
    user = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True)
    pantheon_id = models.PositiveIntegerField(null=True, blank=True, help_text="ID from NEW pantheon")
    updated_information = models.JSONField(default=dict)
    is_applied = models.BooleanField(default=False)

    def __unicode__(self):
        return self.user and self.user.__str__() or None
