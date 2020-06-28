from modeltranslation.translator import TranslationOptions, translator

from settings.models import City, Country


class CountryTranslationOptions(TranslationOptions):
    fields = ["name"]


class CityTranslationOptions(TranslationOptions):
    fields = ["name"]


translator.register(Country, CountryTranslationOptions)
translator.register(City, CityTranslationOptions)
