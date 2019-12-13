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


class TenhouNickname(BaseModel):
    RANKS = [
        [0, u'新人'],
        [1, u'９級'],
        [2, u'８級'],
        [3, u'７級'],
        [4, u'６級'],
        [5, u'５級'],
        [6, u'４級'],
        [7, u'３級'],
        [8, u'２級'],
        [9, u'１級'],
        [10, u'初段'],
        [11, u'二段'],
        [12, u'三段'],
        [13, u'四段'],
        [14, u'五段'],
        [15, u'六段'],
        [16, u'七段'],
        [17, u'八段'],
        [18, u'九段'],
        [19, u'十段'],
        [20, u'天鳳位']
    ]

    objects = TenhouActiveNicknameManager()
    all_objects = models.Manager()

    player = models.ForeignKey(
        Player,
        on_delete=models.CASCADE,
        related_name='tenhou',
    )

    tenhou_username = models.CharField(max_length=8)
    username_created_at = models.DateField()

    last_played_date = models.DateField(null=True, blank=True)

    is_main = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    # DEPRECATED
    rank = models.PositiveSmallIntegerField(choices=RANKS)

    pt = models.PositiveSmallIntegerField(default=0)
    end_pt = models.PositiveSmallIntegerField(default=0)

    average_place = models.DecimalField(decimal_places=2, max_digits=10, default=0)
    played_games = models.PositiveIntegerField(default=0)
    month_average_place = models.DecimalField(decimal_places=2, max_digits=10, default=0)
    month_played_games = models.PositiveIntegerField(default=0)
    four_games_rate = models.DecimalField(decimal_places=2, max_digits=10, default=0)

    def __unicode__(self):
        return self.tenhou_username

    class Meta:
        ordering = ['-rank']
        db_table = 'player_tenhounickname'

    def four_players_aggregated_statistics(self):
        return self.aggregated_statistics.filter(game_players=TenhouAggregatedStatistics.FOUR_PLAYERS).first()

    def all_time_stat(self):
        return self.statistics.filter(stat_type=TenhouStatistics.ALL_TIME)

    def current_month_stat(self):
        return self.statistics.filter(stat_type=TenhouStatistics.CURRENT_MONTH)

    def latest_yakumans(self):
        return self.yakumans.order_by('-date')

    def prepare_latest_places(self):
        return reversed(self.game_logs.filter(game_players=TenhouGameLog.FOUR_PLAYERS).order_by('-game_date')[:20])

    def rank_changes(self):
        return self.game_logs.filter(
            game_players=TenhouGameLog.FOUR_PLAYERS
        ).exclude(rank=F('next_rank')).order_by('game_date')

    def pt_changes(self):
        last_rank_change_date = self.rank_changes().last()
        last_rank_change_date = last_rank_change_date.game_end_date if last_rank_change_date else None
        return self.game_logs.filter(game_date__gte=last_rank_change_date)

    def dan_settings(self):
        return FourPlayersPointsCalculator.DAN_SETTINGS[self.get_rank()]

    def get_rank(self):
        stat = self.aggregated_statistics.filter(game_players=TenhouAggregatedStatistics.FOUR_PLAYERS).first()
        return stat.get_rank_display()


class TenhouAggregatedStatistics(models.Model):
    RANKS = [
        [0, u'新人'],
        [1, u'９級'],
        [2, u'８級'],
        [3, u'７級'],
        [4, u'６級'],
        [5, u'５級'],
        [6, u'４級'],
        [7, u'３級'],
        [8, u'２級'],
        [9, u'１級'],
        [10, u'初段'],
        [11, u'二段'],
        [12, u'三段'],
        [13, u'四段'],
        [14, u'五段'],
        [15, u'六段'],
        [16, u'七段'],
        [17, u'八段'],
        [18, u'九段'],
        [19, u'十段'],
        [20, u'天鳳位']
    ]

    FOUR_PLAYERS = 0
    THREE_PLAYERS = 1

    TYPES = [
        [FOUR_PLAYERS, 'Four players'],
        [THREE_PLAYERS, 'Three players'],
    ]

    tenhou_object = models.ForeignKey(
        TenhouNickname,
        on_delete=models.CASCADE,
        related_name='aggregated_statistics',
    )
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
        db_table = 'portal_tenhou_aggregated_statistics'

    def player(self):
        return self.tenhou_object.player


class TenhouStatistics(models.Model):
    KYU_LOBBY = 0
    DAN_LOBBY = 1
    UPPERDAN_LOBBY = 2
    PHOENIX_LOBBY = 3

    LOBBIES = [
        [KYU_LOBBY, gettext_lazy('Kyu lobby')],
        [DAN_LOBBY, gettext_lazy('Dan lobby')],
        [UPPERDAN_LOBBY, gettext_lazy('Upperdan lobby')],
        [PHOENIX_LOBBY, gettext_lazy('Phoenix lobby')],
    ]

    ALL_TIME = 0
    CURRENT_MONTH = 1
    TYPES = [
        [ALL_TIME, 'All time'],
        [CURRENT_MONTH, 'Current month'],
    ]

    tenhou_object = models.ForeignKey(
        TenhouNickname,
        on_delete=models.CASCADE,
        related_name='statistics',
    )
    lobby = models.PositiveSmallIntegerField(choices=LOBBIES)
    stat_type = models.PositiveSmallIntegerField(choices=TYPES, default=ALL_TIME)

    played_games = models.PositiveIntegerField(default=0)
    average_place = models.DecimalField(decimal_places=2, max_digits=10, default=0)

    first_place = models.DecimalField(decimal_places=2, max_digits=10, default=0)
    second_place = models.DecimalField(decimal_places=2, max_digits=10, default=0)
    third_place = models.DecimalField(decimal_places=2, max_digits=10, default=0)
    fourth_place = models.DecimalField(decimal_places=2, max_digits=10, default=0)

    class Meta:
        ordering = ['lobby']
        db_table = 'portal_tenhou_statistics'


class CollectedYakuman(models.Model):
    tenhou_object = models.ForeignKey(
        TenhouNickname,
        on_delete=models.CASCADE,
        related_name='yakumans',
    )
    date = models.DateTimeField()
    log_id = models.CharField(max_length=44)
    yakuman_list = models.CharField(max_length=60)

    class Meta:
        db_table = 'portal_collected_yakuman'

    def get_log_link(self):
        return 'http://tenhou.net/0/?log={}'.format(self.log_id)

    def yakuman_names(self):
        if not self.yakuman_list:
            return YAKUMAN_CONST.get('kazoe')

        yakuman_list = [int(x) for x in self.yakuman_list.split(',')]
        return ', '.join([str(YAKUMAN_CONST.get(x, x)) for x in yakuman_list])


class TenhouGameLog(models.Model):
    FOUR_PLAYERS = 0
    THREE_PLAYERS = 1

    TYPES = [
        [FOUR_PLAYERS, 'Four players'],
        [THREE_PLAYERS, 'Three players'],
    ]

    tenhou_object = models.ForeignKey(
        TenhouNickname,
        on_delete=models.CASCADE,
        related_name='game_logs',
    )

    lobby = models.PositiveSmallIntegerField(choices=TenhouStatistics.LOBBIES)
    place = models.PositiveSmallIntegerField()
    game_length = models.PositiveSmallIntegerField()
    delta = models.SmallIntegerField(default=0)
    rank = models.PositiveSmallIntegerField(choices=TenhouNickname.RANKS, null=True, blank=True, default=None)
    next_rank = models.PositiveSmallIntegerField(choices=TenhouNickname.RANKS, null=True, blank=True, default=None)
    game_date = models.DateTimeField()
    game_rules = models.CharField(max_length=20)
    game_players = models.PositiveSmallIntegerField(choices=TYPES, null=True, blank=True)

    class Meta:
        unique_together = ['tenhou_object', 'game_date']
        ordering = ['game_date']
        db_table = 'portal_tenhou_game_log'

    @property
    def game_type(self):
        return self.game_rules[2]

    @property
    def game_end_date(self):
        return self.game_date + timedelta(minutes=self.game_length)

    @property
    def badge_class(self):
        if self.rank < self.next_rank:
            return 'success'
        else:
            return 'danger'
