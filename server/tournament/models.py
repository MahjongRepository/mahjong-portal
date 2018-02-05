from django.db import models
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from club.models import Club
from mahjong_portal.models import BaseModel
from player.models import Player
from settings.models import City, Country


class Tournament(BaseModel):
    RIICHI = 0
    MCR = 1

    RR = 'rr'
    CRR = 'crr'
    EMA = 'ema'
    FOREIGN_EMA = 'fema'
    OTHER = 'other'
    ONLINE = 'online'

    GAME_TYPES = [
        [RIICHI, 'Riichi'],
        [MCR, 'MCR']
    ]

    TOURNAMENT_TYPES = [
        [RR, 'rr'],
        [CRR, 'crr'],
        [EMA, 'ema'],
        [FOREIGN_EMA, 'fema'],
        [OTHER, 'other'],
        [ONLINE, 'online'],
    ]

    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, max_length=255)

    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField()

    number_of_sessions = models.PositiveSmallIntegerField(default=0, blank=True)
    number_of_players = models.PositiveSmallIntegerField(default=0, blank=True)
    game_type = models.PositiveSmallIntegerField(choices=GAME_TYPES, default=RIICHI)

    registration_description = models.TextField(null=True, blank=True, default='')
    registration_link = models.URLField(null=True, blank=True, default='')

    clubs = models.ManyToManyField(Club, blank=True)
    country = models.ForeignKey(Country, on_delete=models.PROTECT)
    city = models.ForeignKey(City, on_delete=models.PROTECT, null=True, blank=True)

    tournament_type = models.CharField(max_length=10, choices=TOURNAMENT_TYPES, default=RR)

    is_upcoming = models.BooleanField(default=False)
    need_qualification = models.BooleanField(default=False)
    has_accreditation = models.BooleanField(default=True)
    fill_city_in_registration = models.BooleanField(default=True)

    opened_registration = models.BooleanField(default=False)
    registrations_pre_moderation = models.BooleanField(default=False)

    pantheon_id = models.CharField(max_length=20, null=True, blank=True)

    ema_id = models.CharField(max_length=20, null=True, blank=True)

    def __unicode__(self):
        return self.name

    def get_url(self):
        if self.is_upcoming:
            return reverse('tournament_announcement', kwargs={'slug': self.slug})
        else:
            return reverse('tournament_details', kwargs={'slug': self.slug})

    @property
    def type_badge_class(self):
        if self.is_ema():
            return 'success'

        if self.is_rr():
            return 'primary'

        if self.is_crr():
            return 'info'

        if self.is_online():
            return 'warning'

        return 'info'

    @property
    def type_help_text(self):
        if self.is_ema():
            return 'EMA, RR, CRR'

        if self.is_rr():
            return 'RR, CRR'

        if self.is_crr():
            return 'CRR'

        if self.is_online():
            return 'Online'

        return ''

    @property
    def type_display(self):
        if self.tournament_type == self.FOREIGN_EMA:
            return 'EMA'
        else:
            return self.get_tournament_type_display()

    @property
    def rating_link(self):
        if self.is_online() or self.is_other():
            return '#'

        tournament_type = self.tournament_type
        if tournament_type == self.FOREIGN_EMA:
            tournament_type = self.EMA

        return reverse('rating', kwargs={'slug': tournament_type})

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

    def get_tournament_registrations(self):
        if self.is_online():
            return self.online_tournament_registrations.filter(is_approved=True)
        else:
            return self.tournament_registrations.filter(is_approved=True)


class TournamentResult(BaseModel):
    tournament = models.ForeignKey(Tournament, related_name='results', on_delete=models.PROTECT)
    player = models.ForeignKey(Player, on_delete=models.PROTECT, related_name='tournament_results')
    place = models.PositiveSmallIntegerField()
    scores = models.DecimalField(default=None, decimal_places=2, max_digits=10, null=True, blank=True)

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
    tournament = models.ForeignKey(Tournament, related_name='tournament_registrations', on_delete=models.PROTECT)
    is_approved = models.BooleanField(default=True)

    first_name = models.CharField(max_length=255, verbose_name=_('First name'))
    last_name = models.CharField(max_length=255, verbose_name=_('Last name'))
    city = models.CharField(max_length=255, verbose_name=_('City'))
    phone = models.CharField(max_length=255, verbose_name=_('Phone'),
                             help_text=_('It will be visible only to the administrator'))
    additional_contact = models.CharField(max_length=255, verbose_name=_('Additional contact. Optional'),
                                          help_text=_('It will be visible only to the administrator'),
                                          default='', null=True, blank=True)

    player = models.ForeignKey(Player, null=True, blank=True, related_name='tournament_registrations')
    city_object = models.ForeignKey(City, null=True, blank=True)

    allow_to_save_data = models.BooleanField(default=False, verbose_name=_('I allow to store my personal data'))

    def __unicode__(self):
        return self.full_name

    @property
    def full_name(self):
        return u'{} {}'.format(self.last_name, self.first_name)


class OnlineTournamentRegistration(BaseModel):
    tournament = models.ForeignKey(Tournament, related_name='online_tournament_registrations', on_delete=models.PROTECT)
    is_approved = models.BooleanField(default=True)

    first_name = models.CharField(max_length=255, verbose_name=_('First name'))
    last_name = models.CharField(max_length=255, verbose_name=_('Last name'))
    city = models.CharField(max_length=255, verbose_name=_('City'))
    tenhou_nickname = models.CharField(max_length=255, verbose_name=_('Tenhou.net nickname'))
    contact = models.CharField(max_length=255, verbose_name=_('Your contact (email, phone, etc.)'),
                               help_text=_('It will be visible only to the administrator'))

    player = models.ForeignKey(Player, null=True, blank=True, related_name='online_tournament_registrations')
    city_object = models.ForeignKey(City, null=True, blank=True)

    allow_to_save_data = models.BooleanField(default=False, verbose_name=_('I allow to store my personal data'))

    def __unicode__(self):
        return self.full_name

    @property
    def full_name(self):
        return u'{} {}'.format(self.last_name, self.first_name)


class TournamentApplication(BaseModel):
    text = models.TextField(verbose_name=_('Tell us about your tournament'),
                            help_text=_('We would like to know tournament date, place and your contacts'))

    def __unicode__(self):
        return ''
