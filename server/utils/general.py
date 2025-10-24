# -*- coding: utf-8 -*-

import calendar
import random
import string
from datetime import datetime

import pytz
from django.utils import timezone

from rating.calculation.hardcoded_coefficients import HARDCODED_COEFFICIENTS


def make_random_letters_and_digit_string(length=15):
    random_chars = string.ascii_lowercase + string.digits
    return "".join(random.choice(random_chars) for _ in range(length))


transliteration_table = {
    "а": "a",
    "б": "b",
    "в": "v",
    "г": "g",
    "д": "d",
    "е": "e",
    "ё": "e",
    "ж": "zh",
    "з": "z",
    "и": "i",
    "й": "i",
    "к": "k",
    "л": "l",
    "м": "m",
    "н": "n",
    "о": "o",
    "п": "p",
    "р": "r",
    "с": "s",
    "т": "t",
    "у": "u",
    "ф": "f",
    "х": "kh",
    "ц": "ts",
    "ч": "ch",
    "ш": "sh",
    "щ": "shh",
    "ъ": "ie",
    "ь": "",
    "ы": "y",
    "э": "e",
    "ю": "yu",
    "я": "ya",
}


def transliterate_name(russian_name):
    """
    Russian name to English letters
    with official government transliteration table
    :return:
    """
    transliterated = ""
    for letter in russian_name.lower():
        if letter in transliteration_table:
            transliterated += transliteration_table[letter]
        else:
            transliterated += letter

    return transliterated.title()


def is_date_before(source_date, target_date):
    return target_date.toordinal() - source_date.toordinal() > 0


def is_date_before_or_equals(source_date, target_date):
    return target_date.toordinal() - source_date.toordinal() >= 0


def get_month_first_day(date=None):
    date = date or timezone.now()
    return datetime(date.year, date.month, 1, tzinfo=pytz.utc)


def get_month_last_day(date=None):
    date = date or timezone.now()
    return datetime(date.year, date.month, calendar.monthrange(date.year, date.month)[1], 23, 59, tzinfo=pytz.utc)


# TODO: Remove these hardcoded values when tournaments with stages will be implemented
def get_tournament_coefficient(is_ema, tournament_id, player, default_coefficient):
    if is_ema:
        return default_coefficient

    if HARDCODED_COEFFICIENTS.get(tournament_id):
        return HARDCODED_COEFFICIENTS.get(tournament_id).get(player.id, 0)

    return default_coefficient


def split_name(player_title):
    if " " not in player_title:
        return player_title, ""

    temp = player_title.split(" ")

    first_name = temp[1].title()
    last_name = temp[0].title()
    return first_name, last_name


def format_text(message, kwargs):
    for key, value in kwargs.items():
        formatted_template_key = "%%(%s)s" % key
        if formatted_template_key in message:
            message = message.replace(formatted_template_key, str(value))
        else:
            message = message.replace("%%(%s)" % key, str(value))
    return message
