from django import template
import pymorphy2
from django.utils.translation import get_language

register = template.Library()


@register.filter
def genitive(source_word):
    if get_language() != "ru":
        return source_word

    morph = pymorphy2.MorphAnalyzer()

    word = morph.parse(source_word)[0]
    word = word.inflect({"gent"})

    if not word:
        return source_word

    return word.word


@register.filter
def prepositional(source_word):
    if get_language() != "ru":
        return source_word

    morph = pymorphy2.MorphAnalyzer()

    word = morph.parse(source_word)[0]
    word = word.inflect({"loct"})

    if not word:
        return source_word

    return word.word
