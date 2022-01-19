from django import template
from django.template.defaultfilters import floatformat

from player.tenhou.models import TenhouAggregatedStatistics

register = template.Library()


@register.filter
def display_dan(dan):
    return [x[1] for x in TenhouAggregatedStatistics.RANKS if x[0] == dan][0]


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def percentage(total_items, part):
    if not total_items:
        return floatformat(0, 2)

    return floatformat((part / total_items) * 100, 2)


@register.filter
def display_rate(value):
    """
    Tenhou just use int(rate) to display current player rate
    """
    try:
        return int(value)
    except ValueError:
        return value
