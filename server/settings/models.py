from django.db import models

from mahjong_portal.models import BaseModel


class Country(BaseModel):
    code = models.CharField(max_length=3)
    name = models.CharField(max_length=255)

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return self.name


class City(BaseModel):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return self.name
