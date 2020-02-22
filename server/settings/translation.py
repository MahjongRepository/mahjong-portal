from modeltranslation.translator import translator, TranslationOptions

from settings.models import Country, City


class CountryTranslationOptions(TranslationOptions):
    fields = ["name"]


class CityTranslationOptions(TranslationOptions):
    fields = ["name"]


translator.register(Country, CountryTranslationOptions)
translator.register(City, CityTranslationOptions)
