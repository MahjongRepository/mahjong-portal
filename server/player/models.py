# -*- coding: utf-8 -*-

from django.db import models
from django.db.models import Q
from django.utils.translation import gettext as _

from mahjong_portal.models import BaseModel
from settings.models import City, Country


class Player(BaseModel):
    FEMALE = 0
    MALE = 1
    NONE = 2
    GENDERS = [[FEMALE, "f"], [MALE, "m"], [NONE, ""]]

    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)

    country = models.ForeignKey(Country, on_delete=models.PROTECT, null=True, blank=True)
    city = models.ForeignKey(City, on_delete=models.PROTECT, null=True, blank=True)

    gender = models.PositiveSmallIntegerField(choices=GENDERS, default=NONE)
    is_replacement = models.BooleanField(default=False)
    is_hide = models.BooleanField(default=False)

    ema_id = models.CharField(max_length=30, null=True, blank=True, default="")
    pantheon_id = models.PositiveIntegerField(null=True, blank=True, unique=True)

    class Meta:
        ordering = ["last_name"]

    def __unicode__(self):
        return self.full_name

    def __str__(self):
        return self.__unicode__()

    @property
    def full_name(self):
        if self.is_hide:
            return _("Substitution player")

        return "{} {}".format(self.last_name, self.first_name)

    @property
    def tenhou_object(self):
        tenhou = self.tenhou.all().order_by("-is_main").first()
        return tenhou

    @property
    def ms_object(self):
        ms_obj = self.ms.all().order_by("statistics__rank").first()
        if not ms_obj:
            return None
        return ms_obj.statistics.all().order_by("rank").first()

    @property
    def latest_ema_id(self):
        return int(Player.ema_queryset().first().ema_id)

    @property
    def attaching_request_in_progress(self):
        return self.attaching_request.filter(is_processed=False).exists()

    @property
    def is_verified(self):
        return self.attaching_request.filter(is_processed=True).exists()

    @staticmethod
    def ema_queryset():
        return (
            Player.objects.exclude(Q(ema_id__isnull=True) | Q(ema_id="")).filter(country__code="RU").order_by("-ema_id")
        )


class PlayerTitle(BaseModel):
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="titles")
    text = models.CharField(max_length=255)
    background_color = models.CharField(max_length=7)
    text_color = models.CharField(max_length=7)
    order = models.PositiveIntegerField(default=0)
    url = models.URLField(null=True, blank=True)

    class Meta:
        ordering = ["order"]

    def __unicode__(self):
        return self.text


class PlayerQuotaEvent(BaseModel):
    GREEN = 0
    YELLOW = 1
    ORANGE = 2
    BLUE = 3
    PINK = 4
    GRAY = 5
    DARK_GREEN = 6
    VIOLET = 7
    DARK_BLUE = 8
    NEW = 9

    COLORS = [
        [GREEN, "точно едет"],
        [YELLOW, "скорее всего едет"],
        [ORANGE, "пока сомневается, но скорее всего не едет"],
        [BLUE, "игрок пока ничего не ответил"],
        [PINK, "игрок пока что не проходит, но готов ехать, если появится квота"],
        [GRAY, "точно не едет"],
        [DARK_GREEN, "чемпион"],
        [VIOLET, "игрок замены"],
        [DARK_BLUE, "судья"],
        [NEW, "новая запись"],
    ]

    ERMC_2019 = 0
    WRC_2020 = 1
    TYPES = [[ERMC_2019, "ERMC 2019"], [WRC_2020, "WRC 2020"]]

    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    place = models.PositiveIntegerField(default=None, null=True, blank=True)
    score = models.DecimalField(default=None, decimal_places=2, max_digits=10, null=True, blank=True)

    state = models.PositiveSmallIntegerField(choices=COLORS, default=NEW)
    federation_member = models.BooleanField(default=False, null=True)
    type = models.PositiveSmallIntegerField(choices=TYPES)

    class Meta:
        ordering = ["place"]

    def __unicode__(self):
        return self.player.__unicode__()

    def get_color(self):
        return PlayerQuotaEvent.color_map(self.state)

    @staticmethod
    def color_map(index):
        colors = {
            PlayerQuotaEvent.GREEN: "#93C47D",
            PlayerQuotaEvent.YELLOW: "#FFE599",
            PlayerQuotaEvent.ORANGE: "#F6B26B",
            PlayerQuotaEvent.BLUE: "#C9DAF8",
            PlayerQuotaEvent.PINK: "#D5A6BD",
            PlayerQuotaEvent.GRAY: "#999999",
            PlayerQuotaEvent.DARK_GREEN: "#45818E",
            PlayerQuotaEvent.VIOLET: "#8E7CC3",
            PlayerQuotaEvent.DARK_BLUE: "#5757f8",
            PlayerQuotaEvent.NEW: "#FFFFFF",
        }
        return colors.get(index, "")
