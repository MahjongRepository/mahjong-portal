from django import template

from player.models import PlayerQuotaEvent

register = template.Library()


@register.filter
def ermc_color(color):
    index = {
        "green": PlayerQuotaEvent.GREEN,
        "yellow": PlayerQuotaEvent.YELLOW,
        "orange": PlayerQuotaEvent.ORANGE,
        "blue": PlayerQuotaEvent.BLUE,
        "pink": PlayerQuotaEvent.PINK,
        "gray": PlayerQuotaEvent.GRAY,
        "dark_green": PlayerQuotaEvent.DARK_GREEN,
        "violet": PlayerQuotaEvent.VIOLET,
        "dark_blue": PlayerQuotaEvent.DARK_BLUE,
    }.get(color)

    return PlayerQuotaEvent.color_map(index)
