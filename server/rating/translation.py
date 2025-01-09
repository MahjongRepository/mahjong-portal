# -*- coding: utf-8 -*-

from modeltranslation.translator import TranslationOptions, translator

from rating.models import ExternalRating, Rating


class RatingTranslationOptions(TranslationOptions):
    fields = ["name", "description"]


class ExternalRatingTranslationOptions(TranslationOptions):
    fields = ["name", "description"]


translator.register(Rating, RatingTranslationOptions)
translator.register(ExternalRating, ExternalRatingTranslationOptions)
