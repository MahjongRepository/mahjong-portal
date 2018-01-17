from django.db import models

from mahjong_portal.models import BaseModel


class Country(BaseModel):
    code = models.CharField(max_length=3)
    name = models.CharField(max_length=255)

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return self.name


class City(BaseModel):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return self.name


class TournamentType(BaseModel):
    RR = 'rr'
    CRR = 'crr'
    EMA = 'ema'
    FOREIGN_EMA = 'fema'
    OTHER = 'other'

    # old
    CLUB = 'club'

    TYPES = [
        [RR, 'rr'],
        [CRR, 'crr'],
        [EMA, 'ema'],
        [FOREIGN_EMA, 'fema'],
        [OTHER, 'other']
    ]

    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, choices=TYPES)

    def __unicode__(self):
        return self.name

    @property
    def title(self):
        if self.slug == self.EMA or self.slug == self.FOREIGN_EMA:
            return 'EMA, RR, CRR'

        if self.slug == self.RR:
            return 'RR, CRR'

        if self.slug == self.CRR:
            return 'CRR'

        return ''

    def type_display(self):
        if self.slug == self.FOREIGN_EMA:
            return 'EMA'
        else:
            return self.get_slug_display()

    @property
    def is_ema(self):
        return self.slug == self.EMA or self.slug == self.FOREIGN_EMA

    @property
    def is_rr(self):
        return self.slug == self.RR

    @property
    def is_crr(self):
        return self.slug == self.CRR

    @property
    def badge_class(self):
        if self.slug == self.EMA or self.slug == self.FOREIGN_EMA:
            return 'success'

        if self.slug == self.RR:
            return 'primary'

        if self.slug == self.CRR:
            return 'info'

        return 'info'
