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
