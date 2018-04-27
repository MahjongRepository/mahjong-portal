from django import template

from player.models import TenhouNickname

register = template.Library()


@register.filter
def display_dan(dan):
    return [x[1] for x in TenhouNickname.RANKS if x[0] == dan][0]


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)
