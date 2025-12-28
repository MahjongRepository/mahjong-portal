# -*- coding: utf-8 -*-

from django.db import models

from mahjong_portal.models import BaseModel
from player.models import Player
from tournament.models import Tournament


class PublicYagiKeijiCupManager(models.Manager):
    def get_queryset(self):
        queryset = super(PublicYagiKeijiCupManager, self).get_queryset()
        return queryset.exclude(is_hidden=True)


class YagiKeijiCupSettings(BaseModel):
    is_hidden = models.BooleanField(default=False)
    tenhou_tournament = models.ForeignKey(Tournament, related_name="tenhou_tournament", on_delete=models.PROTECT)
    majsoul_tournament = models.ForeignKey(Tournament, related_name="majsoul_tournament", on_delete=models.PROTECT)
    is_main = models.BooleanField(default=False)

    def __unicode__(self):
        return "Yagi Keiji Cup"


class YagiKeijiCupResults(BaseModel):
    team_name = models.TextField(null=True, blank=True, default="")
    tenhou_player_place = models.PositiveIntegerField(null=True, blank=True)
    tenhou_player_game_count = models.PositiveIntegerField(null=True, blank=True)
    tenhou_player = models.ForeignKey(
        Player, on_delete=models.CASCADE, null=True, blank=True, related_name="yagi_keiji_cup_player_tenhou_results"
    )
    majsoul_player_place = models.PositiveIntegerField(null=True, blank=True)
    majsoul_player_game_count = models.PositiveIntegerField(null=True, blank=True)
    majsoul_player = models.ForeignKey(
        Player, on_delete=models.CASCADE, null=True, blank=True, related_name="yagi_keiji_cup_player_majsoul_results"
    )
    team_scores = models.FloatField(default=0)

    def __unicode__(self):
        return "Yagi Keiji Cup results"
