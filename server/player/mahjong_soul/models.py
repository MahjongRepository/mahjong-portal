# -*- coding: utf-8 -*-

from django.db import models
from django.db.models import Q

from player.mahjong_soul.constants import NEXT_LEVEL_POINTS, RANK_LABELS
from player.models import Player


class MSAccount(models.Model):
    account_id = models.PositiveIntegerField(unique=True)

    account_name = models.CharField(max_length=255, null=True, blank=True)
    last_update = models.CharField(max_length=10, null=True, blank=True)
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="ms")

    def __unicode__(self):
        return "{}, id={}".format(self.account_name, self.account_id)

    def __str__(self):
        return self.__unicode__()

    def four_players_statistics(self):
        return (
            MSAccountStatistic.objects.filter(account=self)
            .filter(game_type=MSAccountStatistic.FOUR_PLAYERS)
            .filter(Q(hanchan_games__gt=0) | Q(tonpusen_games__gt=0))
            .first()
        )

    def three_players_statistics(self):
        return (
            MSAccountStatistic.objects.filter(account=self)
            .filter(game_type=MSAccountStatistic.THREE_PLAYERS)
            .filter(Q(hanchan_games__gt=0) | Q(tonpusen_games__gt=0))
            .first()
        )


class MSAccountStatistic(models.Model):
    FOUR_PLAYERS = 0
    THREE_PLAYERS = 1
    TYPES = [[FOUR_PLAYERS, "Four player"], [THREE_PLAYERS, "Three player"]]

    account = models.ForeignKey(MSAccount, related_name="statistics", on_delete=models.CASCADE)
    game_type = models.PositiveSmallIntegerField(choices=TYPES)
    rank = models.PositiveSmallIntegerField(null=True, blank=True)
    points = models.PositiveSmallIntegerField(null=True, blank=True)

    tonpusen_games = models.PositiveIntegerField(default=0)
    tonpusen_average_place = models.DecimalField(decimal_places=2, max_digits=10, default=0)
    tonpusen_first_place = models.PositiveIntegerField(default=0)
    tonpusen_second_place = models.PositiveIntegerField(default=0)
    tonpusen_third_place = models.PositiveIntegerField(default=0)
    tonpusen_fourth_place = models.PositiveIntegerField(default=0)

    hanchan_games = models.PositiveIntegerField(default=0)
    hanchan_average_place = models.DecimalField(decimal_places=2, max_digits=10, default=0)
    hanchan_first_place = models.PositiveIntegerField(default=0)
    hanchan_second_place = models.PositiveIntegerField(default=0)
    hanchan_third_place = models.PositiveIntegerField(default=0)
    hanchan_fourth_place = models.PositiveIntegerField(default=0)

    def __unicode__(self):
        return "{}, {}".format(self.account.__unicode__(), self.get_rank_display())

    def __str__(self):
        return self.__unicode__()

    @property
    def played_games(self):
        return self.tonpusen_games + self.hanchan_games

    @property
    def last_account_played_date(self):
        if self.game_type == self.FOUR_PLAYERS:
            other_stat = self.account.three_players_statistics()
        else:
            other_stat = self.account.four_players_statistics()
        dates = [self.last_played_date()]
        if other_stat:
            dates.append(other_stat.last_played_date())
        return max([date for date in dates if date is not None])

    def get_rank_display(self):
        return RANK_LABELS.get(self.rank)

    def max_pt(self):
        return NEXT_LEVEL_POINTS.get(self.rank)

    def max_pt_for_chart(self):
        try:
            return int(NEXT_LEVEL_POINTS.get(self.rank))
        except ValueError:
            # for celestial
            return 20000

    def get_points_history_for_latest_rank(self):
        history = MSPointsHistory.objects.filter(stat_object=self).order_by("-rank_index")
        rank_index = getattr(history.first(), "rank_index", None)
        if rank_index is None:
            return MSPointsHistory.objects.none()
        return history.filter(rank_index=rank_index).order_by("created_on")

    def last_played_date(self):
        data = MSPointsHistory.objects.filter(stat_object=self).order_by("-created_on").values("created_on")[:1]
        return data and data.first()["created_on"] or None


class MSPointsHistory(models.Model):
    rank_index = models.PositiveSmallIntegerField()

    stat_object = models.ForeignKey(MSAccountStatistic, on_delete=models.CASCADE)
    rank = models.PositiveSmallIntegerField()
    points = models.PositiveSmallIntegerField()

    created_on = models.DateTimeField(auto_now_add=True)
