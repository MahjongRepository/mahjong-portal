# -*- coding: utf-8 -*-

import ujson as json
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from club.models import Club
from mahjong_portal.models import BaseModel
from player.models import Player
from rating.calculation.hardcoded_coefficients import AGARI_TOURNAMENT_ID
from settings.models import City, Country
from tournament.online_tournament_config import PlainOnlineTournamentConfig


class PublicTournamentManager(models.Manager):
    def get_queryset(self):
        queryset = super(PublicTournamentManager, self).get_queryset()
        return queryset.exclude(is_hidden=True)


class OnlineTournamentConfig(BaseModel):
    token = models.CharField(unique=True, max_length=2048)
    online_config = models.TextField(null=True, blank=True)

    def __unicode__(self):
        return self.token

    def get_config(self):
        try:
            current_config_dict = json.loads(self.online_config)
            en_confirmation_end_time = current_config_dict["en_confirmation_end_time"]
            en_tournament_timezone = current_config_dict["en_tournament_timezone"]
            ru_confirmation_end_time = current_config_dict["ru_confirmation_end_time"]
            ru_tournament_timezone = current_config_dict["ru_tournament_timezone"]
            en_discord_confirmation_channel = current_config_dict["en_discord_confirmation_channel"]
            ru_discord_confirmation_channel = current_config_dict["ru_discord_confirmation_channel"]
            public_lobby = current_config_dict["public_lobby"]
            current_config = PlainOnlineTournamentConfig(
                en_confirmation_end_time,
                en_tournament_timezone,
                ru_confirmation_end_time,
                ru_tournament_timezone,
                en_discord_confirmation_channel,
                ru_discord_confirmation_channel,
                public_lobby,
            )
            current_config.validate()
            return current_config
        except Exception:
            return PlainOnlineTournamentConfig()


class Tournament(BaseModel):
    RIICHI = 0
    MCR = 1

    RR = "rr"
    CRR = "crr"
    EMA = "ema"
    FOREIGN_EMA = "fema"
    OTHER = "other"
    ONLINE = "online"
    CHAMPIONSHIP = "champ"

    GAME_TYPES = [[RIICHI, "Riichi"], [MCR, "MCR"]]

    TOURNAMENT_TYPES = [
        [RR, "rr"],
        [CRR, "crr"],
        [EMA, "ema"],
        [FOREIGN_EMA, "fema"],
        [OTHER, "other"],
        [ONLINE, "online"],
        [CHAMPIONSHIP, "champ."],
    ]

    objects = models.Manager()
    public = PublicTournamentManager()

    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, max_length=255)

    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(db_index=True)

    number_of_sessions = models.PositiveSmallIntegerField(default=0, blank=True)
    number_of_players = models.PositiveSmallIntegerField(default=0, blank=True)

    registration_description = models.TextField(null=True, blank=True, default="")
    registration_link = models.URLField(null=True, blank=True, default="")
    results_description = models.TextField(null=True, blank=True, default="")

    clubs = models.ManyToManyField(Club, blank=True)
    country = models.ForeignKey(Country, on_delete=models.PROTECT)
    city = models.ForeignKey(City, on_delete=models.PROTECT, null=True, blank=True)

    tournament_type = models.CharField(max_length=10, choices=TOURNAMENT_TYPES, default=RR, db_index=True)

    is_upcoming = models.BooleanField(default=False)
    is_hidden = models.BooleanField(default=False)
    is_event = models.BooleanField(default=False)
    is_majsoul_tournament = models.BooleanField(default=False)
    is_pantheon_registration = models.BooleanField(default=False)
    russian_cup = models.BooleanField(default=False)
    fill_city_in_registration = models.BooleanField(default=False)
    opened_registration = models.BooleanField(default=False)
    registrations_pre_moderation = models.BooleanField(default=False)
    is_apply_in_rating = models.BooleanField(default=False)
    is_command = models.BooleanField(default=False, verbose_name="Is team tournament")

    # Sometimes people need to leave notes in registration form
    display_notes = models.BooleanField(default=False)
    # display filled notes in registration table for all in public
    share_notes = models.BooleanField(default=False)

    old_pantheon_id = models.CharField(max_length=20, null=True, blank=True)
    new_pantheon_id = models.CharField(max_length=20, null=True, blank=True)
    ema_id = models.CharField(max_length=20, null=True, blank=True)
    online_config = models.ForeignKey(OnlineTournamentConfig, on_delete=models.PROTECT, null=True, blank=True)

    def __unicode__(self):
        return self.name

    def get_url(self):
        if self.is_upcoming:
            return reverse("tournament_announcement", kwargs={"slug": self.slug})
        else:
            return reverse("tournament_details", kwargs={"slug": self.slug})

    @property
    def type_badge_class(self):
        if self.is_ema():
            return "success"

        if self.is_rr():
            return "primary"

        if self.is_crr():
            return "info"

        if self.is_online():
            return "warning"

        if self.is_championship():
            return "championship"

        return "info"

    @property
    def text_badge_class(self):
        if self.is_online():
            return "text-dark"
        return ""

    @property
    def registration_status_badge_class(self):
        if self.registrations_pre_moderation:
            return "success"

        if self.opened_registration:
            return "primary"

        if not self.opened_registration:
            return "danger"

        if self.is_pantheon_registration:
            return "primary"

        return "primary"

    @property
    def registration_status_help_text(self):
        if self.registrations_pre_moderation:
            return _("premoderation")

        if self.opened_registration:
            return _("open registration")

        if not self.opened_registration:
            return _("registration close")

        if self.is_pantheon_registration:
            return _("open registration")

        return ""

    @property
    def type_help_text(self):
        if self.is_ema():
            return "EMA, RR, CRR"

        if self.is_rr():
            return "RR, CRR"

        if self.is_crr():
            return "CRR"

        if self.is_online():
            return "Online"

        return ""

    @property
    def get_applied_in_rating_text(self):
        return _("Applied in %(rating_type)s rating.") % {
            "rating_type": self.type_help_text,
        }

    @property
    def type_display(self):
        if self.tournament_type == self.FOREIGN_EMA:
            return "EMA"
        else:
            return self.get_tournament_type_display()

    @property
    def rating_link(self):
        if self.is_other() or self.is_championship():
            return ""

        tournament_type = self.tournament_type
        if tournament_type == self.FOREIGN_EMA:
            tournament_type = self.EMA

        return reverse("rating", kwargs={"slug": tournament_type})

    def is_ema(self):
        return self.tournament_type == self.EMA or self.tournament_type == self.FOREIGN_EMA

    def is_rr(self):
        return self.tournament_type == self.RR

    def is_crr(self):
        return self.tournament_type == self.CRR

    def is_online(self):
        return self.tournament_type == self.ONLINE

    def is_other(self):
        return self.tournament_type == self.OTHER

    def is_championship(self):
        return self.tournament_type == self.CHAMPIONSHIP

    def is_stage_tournament(self):
        return self.id == AGARI_TOURNAMENT_ID

    def get_tournament_registrations(self):
        if self.is_online():
            if self.is_majsoul_tournament:
                return self.ms_online_tournament_registrations.filter(is_approved=True)
            else:
                return self.online_tournament_registrations.filter(is_approved=True)
        else:
            return self.tournament_registrations.filter(is_approved=True)

    def championship_tournament_results(self):
        results = TournamentResult.objects.filter(tournament=self).order_by("place")
        if self.tournament_type == Tournament.CHAMPIONSHIP:
            results = results.filter(player__country__code="RU")
        else:
            results = results[:8]
        return results


class TournamentResult(BaseModel):
    tournament = models.ForeignKey(Tournament, related_name="results", on_delete=models.PROTECT)
    player = models.ForeignKey(
        Player, on_delete=models.PROTECT, related_name="tournament_results", null=True, blank=True
    )
    player_string = models.CharField(max_length=512, null=True, blank=True)
    place = models.PositiveSmallIntegerField()
    scores = models.DecimalField(default=None, decimal_places=2, max_digits=10, null=True, blank=True)
    exclude_from_rating = models.BooleanField(default=False)
    games = models.PositiveSmallIntegerField(default=0)

    # for players without profile
    country = models.ForeignKey(Country, on_delete=models.CASCADE, null=True, blank=True)

    def __unicode__(self):
        return self.tournament.name

    @property
    def base_rank(self):
        number_of_players = self.tournament.number_of_players
        place = self.place

        # first place
        if place == 1:
            return 1000

        if place == number_of_players:
            return 0

        return round(((number_of_players - place) / (number_of_players - 1)) * 1000, 2)


class TournamentRegistration(BaseModel):
    tournament = models.ForeignKey(Tournament, related_name="tournament_registrations", on_delete=models.PROTECT)
    is_approved = models.BooleanField(default=True)

    first_name = models.CharField(max_length=255, verbose_name=_("First name"))
    last_name = models.CharField(max_length=255, verbose_name=_("Last name"))
    city = models.CharField(max_length=255, verbose_name=_("City"))
    phone = models.CharField(
        max_length=255, verbose_name=_("Phone"), help_text=_("It will be visible only to the administrator")
    )
    additional_contact = models.CharField(
        max_length=255,
        verbose_name=_("Additional contact. Optional"),
        help_text=_("It will be visible only to the administrator"),
        default="",
        null=True,
        blank=True,
    )

    is_highlighted = models.BooleanField(default=False)
    notes = models.TextField(null=True, blank=True, default="", verbose_name=_("Additional info"))

    player = models.ForeignKey(
        Player, on_delete=models.CASCADE, null=True, blank=True, related_name="tournament_registrations"
    )
    city_object = models.ForeignKey(City, on_delete=models.CASCADE, null=True, blank=True)

    allow_to_save_data = models.BooleanField(default=False, verbose_name=_("I allow to store my personal data"))

    def __unicode__(self):
        return self.full_name

    @property
    def full_name(self):
        return "{} {}".format(self.get_safe_name(self.last_name), self.get_safe_name(self.first_name))

    def get_safe_name(self, name):
        return name if name else ""


class OnlineTournamentRegistration(BaseModel):
    tournament = models.ForeignKey(Tournament, related_name="online_tournament_registrations", on_delete=models.PROTECT)
    is_approved = models.BooleanField(default=True)

    first_name = models.CharField(max_length=255, verbose_name=_("First name"))
    last_name = models.CharField(max_length=255, verbose_name=_("Last name"), null=True, blank=True)
    city = models.CharField(max_length=255, verbose_name=_("City"))
    tenhou_nickname = models.CharField(max_length=255, verbose_name=_("Tenhou.net nickname"), null=True, blank=True)
    is_highlighted = models.BooleanField(default=False)
    contact = models.CharField(
        max_length=255,
        verbose_name=_("Your contact (email, phone, etc.)"),
        help_text=_("It will be visible only to the administrator"),
    )

    player = models.ForeignKey(
        Player, on_delete=models.CASCADE, null=True, blank=True, related_name="online_tournament_registrations"
    )
    user = models.ForeignKey("account.User", on_delete=models.CASCADE, null=True, blank=True)
    city_object = models.ForeignKey(City, on_delete=models.CASCADE, null=True, blank=True)

    allow_to_save_data = models.BooleanField(default=False, verbose_name=_("I allow to store my personal data"))

    notes = models.TextField(null=True, blank=True, default="", verbose_name=_("Additional info"))

    class Meta:
        unique_together = ["tenhou_nickname", "tournament"]

    def __unicode__(self):
        return self.full_name

    @property
    def full_name(self):
        return "{} {}".format(self.get_safe_name(self.last_name), self.get_safe_name(self.first_name))

    def get_safe_name(self, name):
        return name if name else ""


class MsOnlineTournamentRegistration(BaseModel):
    tournament = models.ForeignKey(
        Tournament, related_name="ms_online_tournament_registrations", on_delete=models.PROTECT
    )
    is_approved = models.BooleanField(default=True)

    first_name = models.CharField(max_length=255, verbose_name=_("First name"))
    last_name = models.CharField(max_length=255, verbose_name=_("Last name"), null=True, blank=True)
    city = models.CharField(max_length=255, verbose_name=_("City"))
    ms_nickname = models.CharField(max_length=255, verbose_name="Majsoul nickname")
    ms_friend_id = models.PositiveIntegerField()
    ms_account_id = models.PositiveIntegerField(null=True, blank=True)
    contact = models.CharField(
        null=True,
        blank=True,
        max_length=255,
        verbose_name=_("Your contact (email, phone, etc.)"),
        help_text=_("It will be visible only to the administrator"),
    )

    player = models.ForeignKey(
        Player, on_delete=models.CASCADE, null=True, blank=True, related_name="ms_online_tournament_registrations"
    )
    user = models.ForeignKey("account.User", on_delete=models.CASCADE, null=True, blank=True)
    city_object = models.ForeignKey(City, on_delete=models.CASCADE, null=True, blank=True)

    allow_to_save_data = models.BooleanField(default=False, verbose_name=_("I allow to store my personal data"))

    notes = models.TextField(null=True, blank=True, default="", verbose_name=_("Additional info"))
    is_validated = models.BooleanField(default=False)

    class Meta:
        unique_together = ["ms_nickname", "ms_friend_id", "tournament"]

    def __unicode__(self):
        return self.full_name

    @property
    def full_name(self):
        return "{} {}".format(self.get_safe_name(self.last_name), self.get_safe_name(self.first_name))

    def get_safe_name(self, name):
        return name if name else ""


class TournamentApplication(BaseModel):
    tournament_name = models.CharField(max_length=255, verbose_name=_("Tournament name"))
    city = models.CharField(max_length=255, verbose_name=_("City"))
    tournament_type = models.PositiveSmallIntegerField(
        verbose_name=_("Tournament type"), choices=[[0, "CRR"], [1, "RR"], [2, "EMA"], [3, "OTHER"]], default=0
    )
    start_date = models.CharField(max_length=255, verbose_name=_("Start date"))
    end_date = models.CharField(
        max_length=255,
        verbose_name=_("End date"),
        null=True,
        blank=True,
        help_text=_("Leave empty if tournament has one day"),
    )
    address = models.TextField(verbose_name=_("Address"), help_text=_("How to reach your tournament venue"))
    additional_info_link = models.URLField(
        null=True, blank=True, verbose_name=_("Link to additional tournament information")
    )

    organizer_name = models.CharField(max_length=255, verbose_name=_("Organizer name"))
    organizer_phone = models.CharField(max_length=255, verbose_name=_("Organizer phone"))
    organizer_additional_contact = models.CharField(
        max_length=255,
        verbose_name=_("Organizer additional contact"),
        null=True,
        blank=True,
        help_text=_("Email, link to vk or something else"),
    )

    referee_name = models.CharField(max_length=255, verbose_name=_("Referee name"))
    referee_phone = models.CharField(max_length=255, verbose_name=_("Referee phone"))
    referee_additional_contact = models.CharField(
        max_length=255,
        verbose_name=_("Referee additional contact"),
        null=True,
        blank=True,
        help_text=_("Email, link to vk or something else"),
    )
    referee_english = models.PositiveSmallIntegerField(
        choices=[[0, _("No")], [1, _("Yes")]], default=1, verbose_name=_("Referee english")
    )

    max_number_of_participants = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name=_("Max number of participants")
    )
    number_of_games = models.PositiveSmallIntegerField(verbose_name=_("Number of hanchans"))
    entry_fee = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name=_("Entry fee"), help_text=_("Leave empty if it is free tournament")
    )
    pantheon_needed = models.PositiveSmallIntegerField(
        choices=[[0, _("No")], [1, _("Yes")]], default=1, verbose_name=_("Pantheon needed")
    )
    rules = models.PositiveSmallIntegerField(
        verbose_name=_("Tournament rules"),
        choices=[[0, _("EMA")], [1, _("WRC")], [2, _("JPML-A")], [3, _("JPML-B")], [4, _("Other")]],
        default=0,
    )
    registration_type = models.PositiveSmallIntegerField(
        choices=[[0, _("Open")], [1, _("Closed")], [2, _("Limited")]], verbose_name=_("Registration type"), default=0
    )
    additional_info = models.TextField(
        verbose_name=_("Additional info"), help_text=_("More information about tournament")
    )
    allow_to_save_data = models.BooleanField(help_text=_("I allow to store my personal data"))
    tournament_admin_user = models.ForeignKey("account.User", on_delete=models.SET_NULL, null=True, blank=True)

    def __unicode__(self):
        return ""
