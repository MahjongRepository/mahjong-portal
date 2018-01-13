from django.db import models
from django.contrib.auth.models import AbstractUser

from tournament.models import Tournament


class User(AbstractUser):
    is_tournament_manager = models.BooleanField(default=False)
    managed_tournaments = models.ManyToManyField(Tournament, blank=True)
