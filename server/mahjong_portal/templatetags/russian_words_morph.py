from django import template
import pymorphy2
from django.utils.translation import get_language

register = template.Library()


@register.filter
def genitive(source_word):
    if get_language() != 'ru':
        return source_word

    morph = pymorphy2.MorphAnalyzer()

    word = morph.parse(source_word)[0]
    word = word.inflect({'gent'})

    return word.word
