# -*- coding: utf-8 -*-

from django import template
from django.template.defaultfilters import floatformat

from player.tenhou.models import TenhouAggregatedStatistics

register = template.Library()

CURRENT_MONTH_AGGREGATED_STAT_KEY = "current_month_aggregated_stat"
ALL_AGGREGATED_STAT_KEY = "all_aggregated_stat"


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


@register.filter
def get_current_month_aggregated_stat(tenhou_data_stat, key):
    return tenhou_data_stat[key][CURRENT_MONTH_AGGREGATED_STAT_KEY]


@register.filter
def get_all_aggregated_stat(tenhou_data_stat, key):
    return tenhou_data_stat[key][ALL_AGGREGATED_STAT_KEY]


@register.filter
def get_rank_display(aggregated_stat):
    return aggregated_stat.get_rank_display()


@register.filter
def get_pt(aggregated_stat):
    return aggregated_stat.pt


@register.filter
def get_end_pt(aggregated_stat):
    return aggregated_stat.end_pt


@register.filter
def get_rate(aggregated_stat):
    return aggregated_stat.rate
