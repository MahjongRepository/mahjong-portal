# -*- coding: utf-8 -*-

from datetime import timedelta

from django.db import models
from django.db.models import F
from django.utils.translation import gettext_lazy

from mahjong_portal.models import BaseModel
from player.models import Player
from utils.tenhou.points_calculator import FourPlayersPointsCalculator
from utils.tenhou.yakuman_list import YAKUMAN_CONST


class TenhouActiveNicknameManager(models.Manager):
    def get_queryset(self):
        queryset = super(TenhouActiveNicknameManager, self).get_queryset()
        return queryset.filter(is_active=True)


class TenhouAllNicknameManager(models.Manager):
    def get_queryset(self):
        return super(TenhouAllNicknameManager, self).get_queryset()


class TenhouNickname(BaseModel):
    objects = TenhouAllNicknameManager()
    active_objects = TenhouActiveNicknameManager()
    all_objects = models.Manager()

    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="tenhou")

    tenhou_username = models.CharField(max_length=8)
    username_created_at = models.DateField()

    last_played_date = models.DateField(null=True, blank=True)

    is_main = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    def __unicode__(self):
        return self.tenhou_username

    class Meta:
        ordering = ["-username_created_at"]
        db_table = "player_tenhounickname"

    def four_players_aggregated_statistics(self):
        return self.aggregated_statistics.filter(game_players=TenhouAggregatedStatistics.FOUR_PLAYERS).first()

    def all_time_stat(self):
        return self.statistics.filter(stat_type=TenhouStatistics.ALL_TIME)

    def current_month_stat(self):
        return self.statistics.filter(stat_type=TenhouStatistics.CURRENT_MONTH)

    def latest_yakumans(self):
        return self.yakumans.order_by("-date")

    def prepare_latest_places(self):
        return list(
            reversed(self.game_logs.filter(game_players=TenhouGameLog.FOUR_PLAYERS).order_by("-game_date")[:20])
        )

    def rank_changes(self):
        return (
            self.game_logs.filter(game_players=TenhouGameLog.FOUR_PLAYERS)
            .exclude(rank=F("next_rank"))
            .order_by("game_date")
        )

    def pt_changes(self):
        last_rank_change_date = self.rank_changes().last()
        last_rank_change_date = last_rank_change_date.game_end_date if last_rank_change_date else None
        if not last_rank_change_date:
            return None
        return self.game_logs.filter(game_date__gte=last_rank_change_date)

    def dan_settings(self):
        rank = self.get_rank_display()
        if rank and rank != "":
            return FourPlayersPointsCalculator.DAN_SETTINGS[rank]

    def get_rank_display(self):
        stat = self.aggregated_statistics.filter(game_players=TenhouAggregatedStatistics.FOUR_PLAYERS).first()
        if stat:
            return stat.get_rank_display()
        else:
            return ""


class TenhouAggregatedStatistics(models.Model):
    RANKS = [
        [0, "新人"],
        [1, "９級"],
        [2, "８級"],
        [3, "７級"],
        [4, "６級"],
        [5, "５級"],
        [6, "４級"],
        [7, "３級"],
        [8, "２級"],
        [9, "１級"],
        [10, "初段"],
        [11, "二段"],
        [12, "三段"],
        [13, "四段"],
        [14, "五段"],
        [15, "六段"],
        [16, "七段"],
        [17, "八段"],
        [18, "九段"],
        [19, "十段"],
        [20, "天鳳位"],
    ]

    FOUR_PLAYERS = 0
    THREE_PLAYERS = 1

    TYPES = [[FOUR_PLAYERS, "Four players"], [THREE_PLAYERS, "Three players"]]

    tenhou_object = models.ForeignKey(TenhouNickname, on_delete=models.CASCADE, related_name="aggregated_statistics")
    rank = models.PositiveSmallIntegerField(choices=RANKS, null=True, blank=True)
    rate = models.DecimalField(decimal_places=2, max_digits=10, default=0)
    game_players = models.PositiveSmallIntegerField(choices=TYPES, null=True, blank=True)

    played_games = models.PositiveIntegerField(default=0)
    month_played_games = models.PositiveIntegerField(default=0)

    average_place = models.DecimalField(decimal_places=2, max_digits=10, default=0)
    month_average_place = models.DecimalField(decimal_places=2, max_digits=10, default=0)

    pt = models.PositiveSmallIntegerField(default=0)
    end_pt = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "portal_tenhou_aggregated_statistics"

    def player(self):
        return self.tenhou_object.player


class TenhouStatistics(models.Model):
    KYU_LOBBY = 0
    DAN_LOBBY = 1
    UPPERDAN_LOBBY = 2
    PHOENIX_LOBBY = 3

    LOBBIES = [
        [KYU_LOBBY, gettext_lazy("Ippan")],
        [DAN_LOBBY, gettext_lazy("Joukyuu")],
        [UPPERDAN_LOBBY, gettext_lazy("Tokujou")],
        [PHOENIX_LOBBY, gettext_lazy("Houou")],
    ]

    ALL_TIME = 0
    CURRENT_MONTH = 1
    TYPES = [[ALL_TIME, "All time"], [CURRENT_MONTH, "Current month"]]

    tenhou_object = models.ForeignKey(TenhouNickname, on_delete=models.CASCADE, related_name="statistics")
    lobby = models.PositiveSmallIntegerField(choices=LOBBIES)
    stat_type = models.PositiveSmallIntegerField(choices=TYPES, default=ALL_TIME)

    played_games = models.PositiveIntegerField(default=0)
    average_place = models.DecimalField(decimal_places=2, max_digits=10, default=0)

    first_place = models.DecimalField(decimal_places=2, max_digits=10, default=0)
    second_place = models.DecimalField(decimal_places=2, max_digits=10, default=0)
    third_place = models.DecimalField(decimal_places=2, max_digits=10, default=0)
    fourth_place = models.DecimalField(decimal_places=2, max_digits=10, default=0)

    class Meta:
        ordering = ["lobby"]
        db_table = "portal_tenhou_statistics"


class CollectedYakuman(models.Model):
    tenhou_object = models.ForeignKey(TenhouNickname, on_delete=models.CASCADE, related_name="yakumans")
    date = models.DateTimeField()
    log_id = models.CharField(max_length=44)
    yakuman_list = models.CharField(max_length=60)

    class Meta:
        db_table = "portal_collected_yakuman"

    def get_log_link(self):
        return "http://tenhou.net/0/?log={}".format(self.log_id)

    def yakuman_names(self):
        if not self.yakuman_list:
            return YAKUMAN_CONST.get("kazoe")

        yakuman_list = [int(x) for x in self.yakuman_list.split(",")]
        return ", ".join([str(YAKUMAN_CONST.get(x, x)) for x in yakuman_list])


class TenhouGameLog(models.Model):
    FOUR_PLAYERS = 0
    THREE_PLAYERS = 1

    TYPES = [[FOUR_PLAYERS, "Four players"], [THREE_PLAYERS, "Three players"]]

    tenhou_object = models.ForeignKey(TenhouNickname, on_delete=models.CASCADE, related_name="game_logs")

    lobby = models.PositiveSmallIntegerField(choices=TenhouStatistics.LOBBIES)
    place = models.PositiveSmallIntegerField()
    game_length = models.PositiveSmallIntegerField()
    delta = models.SmallIntegerField(default=0)
    rank = models.PositiveSmallIntegerField(
        choices=TenhouAggregatedStatistics.RANKS, null=True, blank=True, default=None
    )
    next_rank = models.PositiveSmallIntegerField(
        choices=TenhouAggregatedStatistics.RANKS, null=True, blank=True, default=None
    )
    game_date = models.DateTimeField()
    game_rules = models.CharField(max_length=20)
    game_players = models.PositiveSmallIntegerField(choices=TYPES, null=True, blank=True)

    class Meta:
        unique_together = ["tenhou_object", "game_date"]
        ordering = ["game_date"]
        db_table = "portal_tenhou_game_log"

    @property
    def game_type(self):
        return self.game_rules[2]

    @property
    def game_end_date(self):
        return self.game_date + timedelta(minutes=self.game_length)

    @property
    def badge_class(self):
        if self.rank < self.next_rank:
            return "success"
        else:
            return "danger"
