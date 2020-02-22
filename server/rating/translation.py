from modeltranslation.translator import translator, TranslationOptions

from rating.models import Rating


class RatingTranslationOptions(TranslationOptions):
    fields = ["name", "description"]


translator.register(Rating, RatingTranslationOptions)
