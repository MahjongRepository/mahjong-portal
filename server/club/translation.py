# -*- coding: utf-8 -*-

from modeltranslation.translator import TranslationOptions, translator

from club.models import Club


class ClubTranslationOptions(TranslationOptions):
    fields = ["name", "description"]


translator.register(Club, ClubTranslationOptions)
