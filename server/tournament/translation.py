from modeltranslation.translator import TranslationOptions, translator

from tournament.models import Tournament


class TournamentTranslationOptions(TranslationOptions):
    fields = ["name", "registration_description", "results_description"]


translator.register(Tournament, TournamentTranslationOptions)
