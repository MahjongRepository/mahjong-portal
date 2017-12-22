from django.db import models

from leaderboard.models import BaseModel


class Country(BaseModel):
    code = models.CharField(max_length=3)
    name = models.CharField(max_length=255)

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return self.name

    def __str__(self):
        return self.__unicode__()


class City(BaseModel):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return self.name

    def __str__(self):
        return self.__unicode__()


class TournamentType(BaseModel):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
