# -*- coding: utf-8 -*-

from django.db import models

from mahjong_portal.models import BaseModel
from player.models import Player
from settings.models import City, Country


class Club(BaseModel):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    website = models.URLField(null=True, blank=True)
    timezone = models.CharField(max_length=255, null=True, blank=True)

    description = models.TextField(null=True, blank=True)

    players = models.ManyToManyField(Player, related_name="clubs", blank=True)

    country = models.ForeignKey(Country, on_delete=models.PROTECT)
    city = models.ForeignKey(City, on_delete=models.PROTECT, null=True, blank=True)

    lat = models.DecimalField(max_digits=21, decimal_places=15, null=True, blank=True)
    lng = models.DecimalField(max_digits=21, decimal_places=15, null=True, blank=True)

    pantheon_ids = models.CharField(max_length=255, null=True, blank=True)
    new_pantheon_ids = models.CharField(max_length=255, null=True, blank=True)
    current_club_rating_pantheon_id = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        ordering = ["name"]

    def __unicode__(self):
        return self.name

    def get_link_to_club_rating(self, event_id=None):
        if not event_id:
            event_id = self.current_club_rating_pantheon_id
        return f"https://rating.riichimahjong.org/event/{event_id}/order/rating"

    def get_archive_link_to_club_rating(self, event_id=None):
        if not event_id:
            event_id = self.current_club_rating_pantheon_id
        return f"https://archive.riichimahjong.org/eid{event_id}/stat.html"

    def get_links_to_previous_games(self):
        ids = sorted([int(x) for x in self.pantheon_ids.split(",")], reverse=True)
        return [self.get_archive_link_to_club_rating(x) for x in ids]

    def get_all_pantheon_ids(self):
        ids = []
        if self.pantheon_ids:
            ids.extend(self.pantheon_ids.split(","))
        if self.current_club_rating_pantheon_id:
            ids.append(self.current_club_rating_pantheon_id)
        return ids
