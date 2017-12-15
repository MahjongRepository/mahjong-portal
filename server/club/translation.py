from modeltranslation.translator import translator, TranslationOptions

from club.models import Club


class ClubTranslationOptions(TranslationOptions):
    fields = ['name']


translator.register(Club, ClubTranslationOptions)
