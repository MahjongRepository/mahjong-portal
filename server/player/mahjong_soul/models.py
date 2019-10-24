from django.db import models

from player.mahjong_soul.constants import NEXT_LEVEL_POINTS, RANK_LABELS
from player.models import Player


class MSAccount(models.Model):
    account_id = models.PositiveIntegerField(unique=True)

    account_name = models.CharField(max_length=255, null=True, blank=True)
    player = models.ForeignKey(
        Player,
        on_delete=models.CASCADE,
        related_name='ms',
    )


class MSAccountStatistic(models.Model):
    FOUR_PLAYERS = 0
    THREE_PLAYERS = 1
    TYPES = [
        [FOUR_PLAYERS, 'Four player'],
        [THREE_PLAYERS, 'Three player'],
    ]

    account = models.ForeignKey(
        MSAccount,
        related_name='statistics',
        on_delete=models.CASCADE
    )
    game_type = models.PositiveSmallIntegerField(choices=TYPES)
    rank = models.PositiveSmallIntegerField(null=True, blank=True)
    points = models.PositiveSmallIntegerField(null=True, blank=True)

    tonpusen_games = models.PositiveIntegerField(default=0)
    tonpusen_average_place = models.DecimalField(decimal_places=2, max_digits=10, default=0)
    tonpusen_first_place = models.DecimalField(decimal_places=2, max_digits=10, default=0)
    tonpusen_second_place = models.DecimalField(decimal_places=2, max_digits=10, default=0)
    tonpusen_third_place = models.DecimalField(decimal_places=2, max_digits=10, default=0)
    tonpusen_fourth_place = models.DecimalField(decimal_places=2, max_digits=10, default=0)

    hanchan_games = models.PositiveIntegerField(default=0)
    hanchan_average_place = models.DecimalField(decimal_places=2, max_digits=10, default=0)
    hanchan_first_place = models.DecimalField(decimal_places=2, max_digits=10, default=0)
    hanchan_second_place = models.DecimalField(decimal_places=2, max_digits=10, default=0)
    hanchan_third_place = models.DecimalField(decimal_places=2, max_digits=10, default=0)
    hanchan_fourth_place = models.DecimalField(decimal_places=2, max_digits=10, default=0)

    def get_rank_display(self):
        return RANK_LABELS.get(self.rank)

    def max_pt(self):
        return NEXT_LEVEL_POINTS.get(self.rank)
