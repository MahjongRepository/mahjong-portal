from modeltranslation.translator import TranslationOptions, translator

from rating.models import Rating


class RatingTranslationOptions(TranslationOptions):
    fields = ["name", "description"]


translator.register(Rating, RatingTranslationOptions)
