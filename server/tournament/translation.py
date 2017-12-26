from modeltranslation.translator import translator, TranslationOptions

from settings.models import TournamentType
from tournament.models import Tournament


class TournamentTypeTranslationOptions(TranslationOptions):
    fields = ['name']


class TournamentTranslationOptions(TranslationOptions):
    fields = ['name', 'registration_description']


translator.register(TournamentType, TournamentTypeTranslationOptions)
translator.register(Tournament, TournamentTranslationOptions)
