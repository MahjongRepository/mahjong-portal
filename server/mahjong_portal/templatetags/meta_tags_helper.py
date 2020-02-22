from django import template
from django.template.defaultfilters import date
from django.utils.translation import gettext as _

from mahjong_portal.templatetags.russian_words_morph import prepositional, genitive

register = template.Library()


@register.simple_tag
def tournaments_list_title(tournament_type, current_year):
    if tournament_type:
        return _("EMA tournaments tournaments during %d") % current_year
    else:
        return _("Tournaments tournaments during %d") % current_year


@register.simple_tag
def tournaments_list_description(tournament_type, current_year):
    if tournament_type:
        return _("List of EMA riichi mahjong tournaments during %d") % current_year
    else:
        return _("List of riichi mahjong tournaments during %d") % current_year


@register.simple_tag
def tournament_page_description(tournament):
    if tournament.city:
        place = "{}, {}".format(
            prepositional(tournament.city.name).title(), tournament.country
        )
    else:
        place = "{}".format(prepositional(tournament.country.name).title())

    return _('Riichi mahjong tournament "%(name)s" held %(date)s in %(place)s') % {
        "name": tournament.name,
        "date": date(tournament.end_date),
        "place": place,
    }


@register.simple_tag
def club_page_description(club):
    if club.city:
        place = "{}, {}".format(prepositional(club.city.name).title(), club.country)
    else:
        place = "{}".format(prepositional(club.country.name).title())

    return _('Riichi mahjong club "%(name)s" in %(place)s') % {
        "name": club.name,
        "place": place,
    }


@register.simple_tag
def player_page_description(player):
    if player.city:
        place = "{}, {}".format(genitive(player.city.name).title(), player.country)
    else:
        place = "{}".format(genitive(player.country.name).title())

    return _("Riichi mahjong player %(name)s from %(place)s") % {
        "name": player.full_name,
        "place": place,
    }
