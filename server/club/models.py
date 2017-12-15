from django.db import models

from leaderboard.models import BaseModel
from player.models import Player
from settings.models import City, Country


class Club(BaseModel):
    name = models.CharField(max_length=255)
    slug = models.SlugField()
    website = models.URLField(null=True, blank=True)

    players = models.ManyToManyField(Player, related_name='clubs')

    country = models.ForeignKey(Country, on_delete=models.PROTECT)
    city = models.ForeignKey(City, on_delete=models.PROTECT, null=True, blank=True)


