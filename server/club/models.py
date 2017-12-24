from django.db import models

from leaderboard.models import BaseModel
from player.models import Player
from settings.models import City, Country


class Club(BaseModel):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    website = models.URLField(null=True, blank=True)

    players = models.ManyToManyField(Player, related_name='clubs', blank=True)

    country = models.ForeignKey(Country, on_delete=models.PROTECT)
    city = models.ForeignKey(City, on_delete=models.PROTECT, null=True, blank=True)

    lat = models.DecimalField(max_digits=21, decimal_places=15, null=True, blank=True)
    lng = models.DecimalField(max_digits=21, decimal_places=15, null=True, blank=True)

    def __unicode__(self):
        return self.name
