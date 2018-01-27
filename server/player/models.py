from django.db import models
from django.utils.translation import gettext as _

from mahjong_portal.models import BaseModel
from settings.models import Country, City


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
        [1, u'9級'],
        [2, u'8級'],
        [3, u'7級'],
        [4, u'6級'],
        [5, u'5級'],
        [6, u'4級'],
        [7, u'3級'],
        [8, u'2級'],
        [9, u'1級'],
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

    def __unicode__(self):
        return self.tenhou_username
