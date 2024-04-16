# -*- coding: utf-8 -*-

from modeltranslation.translator import TranslationOptions, translator

from league.models import League


class LeagueTranslationOptions(TranslationOptions):
    fields = ["name", "description"]


translator.register(League, LeagueTranslationOptions)
