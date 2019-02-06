from django import template

from player.models import PlayerERMC

register = template.Library()


@register.filter
def ermc_color(color):
    index = {
        'green': PlayerERMC.GREEN,
        'yellow': PlayerERMC.YELLOW,
        'orange': PlayerERMC.ORANGE,
        'blue': PlayerERMC.BLUE,
        'pink': PlayerERMC.PINK,
        'gray': PlayerERMC.GRAY,
        'dark_green': PlayerERMC.DARK_GREEN,
        'violet': PlayerERMC.VIOLET,
    }.get(color)

    return PlayerERMC.color_map(index)
