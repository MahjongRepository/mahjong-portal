from django.db import models
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from mahjong_portal.models import BaseModel
from settings.models import Country, City
from utils.tenhou.yakuman_list import YAKUMAN_CONST


class PlayerManager(models.Manager):
    
    def get_queryset(self):
        # don't show hidden players in the lists
        return (super(PlayerManager, self).get_queryset()
                                          .exclude(is_hide=True)
                                          .exclude(is_replacement=True))


class Player(BaseModel):
    FEMALE = 0
    MALE = 1
    NONE = 2
    GENDERS = [
        [FEMALE, 'f'],
        [MALE, 'm'],
        [NONE, ''],
    ]
    
    objects = PlayerManager()
    all_objects = models.Manager()

    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)

    country = models.ForeignKey(Country, on_delete=models.PROTECT, null=True, blank=True)
    city = models.ForeignKey(City, on_delete=models.PROTECT, null=True, blank=True)

    gender = models.PositiveSmallIntegerField(choices=GENDERS, default=NONE)
    is_replacement = models.BooleanField(default=False)
    is_hide = models.BooleanField(default=False)

    ema_id = models.CharField(max_length=30, null=True, blank=True, default='')
    pantheon_id = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ['last_name']

    def __unicode__(self):
        return self.full_name

    def __str__(self):
        return self.__unicode__()

    @property
    def full_name(self):
        if self.is_hide:
            return _('Substitution player')
        
        return u'{} {}'.format(self.last_name, self.first_name)

    @property
    def tenhou_object(self):
        tenhou = self.tenhou.all().order_by('-rank').first()
        return tenhou


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

    def all_time_stat(self):
        return self.statistics.filter(stat_type=TenhouStatistics.ALL_TIME)

    def current_month_stat(self):
        return self.statistics.filter(stat_type=TenhouStatistics.CURRENT_MONTH)

    def latest_yakumans(self):
        return self.yakumans.order_by('-date')


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


class CollectedYakuman(models.Model):
    tenhou_object = models.ForeignKey(TenhouNickname, related_name='yakumans')
    date = models.DateTimeField()
    log_id = models.CharField(max_length=44)
    yakuman_list = models.CharField(max_length=60)

    def get_log_link(self):
        return 'http://tenhou.net/0/?log={}'.format(self.log_id)

    def yakuman_names(self):
        if not self.yakuman_list:
            return YAKUMAN_CONST.get('kazoe')

        yakuman_list = [int(x) for x in self.yakuman_list.split(',')]
        return ','.join([str(YAKUMAN_CONST.get(x, x)) for x in yakuman_list])
