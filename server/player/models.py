from django.db import models

from leaderboard.models import BaseModel
from settings.models import Country, City


class Player(BaseModel):
    FEMALE = 0
    MALE = 1
    NONE = 2
    GENDERS = [
        [FEMALE, 'f'],
        [MALE, 'm'],
        [NONE, ''],
    ]

    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)

    country = models.ForeignKey(Country, on_delete=models.PROTECT)
    city = models.ForeignKey(City, on_delete=models.PROTECT, null=True, blank=True)

    gender = models.PositiveSmallIntegerField(choices=GENDERS, default=NONE)
    is_replacement = models.BooleanField(default=False)
    is_hide = models.BooleanField(default=False)
