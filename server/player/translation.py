from modeltranslation.translator import translator, TranslationOptions

from player.models import Player


class PlayerTranslationOptions(TranslationOptions):
    fields = ['first_name', 'last_name']


translator.register(Player, PlayerTranslationOptions)
