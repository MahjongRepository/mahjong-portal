from django.db import models
from django.db.models import Q
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
        tenhou = self.tenhou.all().order_by('-is_main').first()
        return tenhou

    @property
    def latest_ema_id(self):
        return int(Player.ema_queryset().first().ema_id)

    @staticmethod
    def ema_queryset():
        return (Player.objects
                .exclude(Q(ema_id__isnull=True) | Q(ema_id=''))
                .filter(country__code='RU')
                .order_by('-ema_id'))


class PlayerERMC(BaseModel):
    GREEN = 0
    YELLOW = 1
    ORANGE = 2
    BLUE = 3
    PINK = 4
    GRAY = 5
    DARK_GREEN = 6
    VIOLET = 7
    DARK_BLUE = 8

    COLORS = [
        [GREEN, 'точно едет'],
        [YELLOW, 'скорее всего едет'],
        [ORANGE, 'пока сомневается, но скорее всего не едет'],
        [BLUE, 'игрок пока ничего не ответил'],
        [PINK, 'игрок пока что не проходит, но готов ехать, если появится квота'],
        [GRAY, 'точно не едет'],
        [DARK_GREEN, 'деда'],
        [VIOLET, 'игрок замены'],
        [DARK_BLUE, 'не деда (судья)'],
    ]

    player = models.OneToOneField(Player, on_delete=models.CASCADE, related_name='ermc')

    state = models.PositiveSmallIntegerField(choices=COLORS)
    federation_member = models.BooleanField(default=False)

    def __unicode__(self):
        return self.player.__unicode__()

    def get_color(self):
        return PlayerERMC.color_map(self.state)

    @staticmethod
    def color_map(index):
        colors = {
            PlayerERMC.GREEN: '#93C47D',
            PlayerERMC.YELLOW: '#FFE599',
            PlayerERMC.ORANGE: '#F6B26B',
            PlayerERMC.BLUE: '#C9DAF8',
            PlayerERMC.PINK: '#D5A6BD',
            PlayerERMC.GRAY: '#999999',
            PlayerERMC.DARK_GREEN: '#45818E',
            PlayerERMC.VIOLET: '#8E7CC3',
            PlayerERMC.DARK_BLUE: '#5757f8',
        }
        return colors.get(index, '')
