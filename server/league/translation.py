# -*- coding: utf-8 -*-

from modeltranslation.translator import TranslationOptions, translator

from player.models import Player, PlayerTitle


class PlayerTranslationOptions(TranslationOptions):
    fields = ["first_name", "last_name"]


class PlayerTitleOptions(TranslationOptions):
    fields = ["text"]


translator.register(Player, PlayerTranslationOptions)
translator.register(PlayerTitle, PlayerTitleOptions)
