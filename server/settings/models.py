from django.db import models

from leaderboard.models import BaseModel


class Country(BaseModel):
    code = models.CharField(max_length=3)
    name = models.CharField(max_length=255)


class City(BaseModel):
    name = models.CharField(max_length=255)
    slug = models.SlugField()


class TournamentType(BaseModel):
    name = models.CharField(max_length=255)
    slug = models.SlugField()
