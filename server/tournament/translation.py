from modeltranslation.translator import translator, TranslationOptions

from tournament.models import Tournament


class TournamentTranslationOptions(TranslationOptions):
    fields = ['name', 'registration_description']


translator.register(Tournament, TournamentTranslationOptions)
