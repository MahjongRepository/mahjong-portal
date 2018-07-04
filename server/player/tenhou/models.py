from datetime import timedelta

from django.db import models
from django.utils.translation import gettext_lazy

from mahjong_portal.models import BaseModel
from player.models import Player
from utils.tenhou.yakuman_list import YAKUMAN_CONST


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

    player = models.ForeignKey(Player, related_name='tenhou')

    tenhou_username = models.CharField(max_length=8)
    username_created_at = models.DateField()

    rank = models.PositiveSmallIntegerField(choices=RANKS)

    average_place = models.DecimalField(decimal_places=2, max_digits=10, default=0)
    played_games = models.PositiveIntegerField(default=0)
    month_average_place = models.DecimalField(decimal_places=2, max_digits=10, default=0)
    month_played_games = models.PositiveIntegerField(default=0)
    four_games_rate = models.DecimalField(decimal_places=2, max_digits=10, default=0)

    pt = models.PositiveSmallIntegerField(default=0)
    end_pt = models.PositiveSmallIntegerField(default=0)
    last_played_date = models.DateField(null=True, blank=True)

    is_main = models.BooleanField(default=True)

    def __unicode__(self):
        return self.tenhou_username

    class Meta:
        ordering = ['-rank']
        db_table = 'player_tenhounickname'

    def all_time_stat(self):
        return self.statistics.filter(stat_type=TenhouStatistics.ALL_TIME)

    def current_month_stat(self):
        return self.statistics.filter(stat_type=TenhouStatistics.CURRENT_MONTH)

    def latest_yakumans(self):
        return self.yakumans.order_by('-date')

    def prepare_latest_places(self):
        return reversed(self.game_logs.order_by('-game_date')[:20])


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

    tenhou_object = models.ForeignKey(TenhouNickname, related_name='statistics')
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
    tenhou_object = models.ForeignKey(TenhouNickname, related_name='yakumans')
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
    tenhou_object = models.ForeignKey(TenhouNickname, related_name='game_logs')

    lobby = models.PositiveSmallIntegerField(choices=TenhouStatistics.LOBBIES)
    place = models.PositiveSmallIntegerField()
    game_length = models.PositiveSmallIntegerField()
    delta = models.SmallIntegerField(default=0)
    rank = models.PositiveSmallIntegerField(choices=TenhouNickname.RANKS, null=True, blank=True, default=None)
    game_date = models.DateTimeField()
    game_rules = models.CharField(max_length=20)

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
