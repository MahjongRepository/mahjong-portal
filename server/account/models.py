from django.contrib.auth.models import AbstractUser
from django.db import models

from tournament.models import Tournament


class User(AbstractUser):
    is_tournament_manager = models.BooleanField(default=False)
    is_ema_players_manager = models.BooleanField(default=False)
    managed_tournaments = models.ManyToManyField(Tournament, blank=True)
