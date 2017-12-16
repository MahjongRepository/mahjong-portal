from django.db import models

from leaderboard.models import BaseModel
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

    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)

    country = models.ForeignKey(Country, on_delete=models.PROTECT)
    city = models.ForeignKey(City, on_delete=models.PROTECT, null=True, blank=True)

    gender = models.PositiveSmallIntegerField(choices=GENDERS, default=NONE)
    is_replacement = models.BooleanField(default=False)
    is_hide = models.BooleanField(default=False)

    inner_rating_score = models.DecimalField(default=0, decimal_places=2, max_digits=10)
    inner_rating_place = models.PositiveIntegerField(default=0)

    @property
    def full_name(self):
        return ' '.join([self.first_name, self.last_name])
