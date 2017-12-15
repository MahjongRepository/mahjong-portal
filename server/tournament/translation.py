from modeltranslation.translator import translator, TranslationOptions

from club.models import Club
from settings.models import TournamentType
from tournament.models import Tournament


class TournamentTypeTranslationOptions(TranslationOptions):
    fields = ['name']


class TournamentTranslationOptions(TranslationOptions):
    fields = ['name']


translator.register(TournamentType, TournamentTypeTranslationOptions)
translator.register(Tournament, TournamentTranslationOptions)
