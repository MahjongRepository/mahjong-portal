from django.contrib.auth.models import AbstractUser
from django.db import models

from mahjong_portal.models import BaseModel
from player.models import Player
from tournament.models import Tournament


class User(AbstractUser):
    is_tournament_manager = models.BooleanField(default=False)
    is_ema_players_manager = models.BooleanField(default=False)
    managed_tournaments = models.ManyToManyField(Tournament, blank=True)

    attached_player = models.ForeignKey(Player, null=True, blank=True, on_delete=models.PROTECT)


class AttachingPlayerRequest(BaseModel):
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    player = models.ForeignKey(Player, on_delete=models.PROTECT)
    is_processed = models.BooleanField(default=False)
