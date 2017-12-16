from modeltranslation.translator import translator, TranslationOptions

from rating.models import Rating


class RatingTranslationOptions(TranslationOptions):
    fields = ['name']


translator.register(Rating, RatingTranslationOptions)
