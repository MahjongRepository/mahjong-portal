import calendar
import string
import random
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


def get_month_first_day(date=None):
    date = date or timezone.now()
    return datetime(date.year, date.month, 1, tzinfo=pytz.utc)


def get_month_last_day(date=None):
    date = date or timezone.now()
    return datetime(
        date.year,
        date.month,
        calendar.monthrange(date.year, date.month)[1],
        23,
        59,
        tzinfo=pytz.utc,
    )


# TODO: Remove these hardcoded values when tournaments with stages will be implemented
def get_tournament_coefficient(is_ema, tournament_id, player, default_coefficient):
    if is_ema:
        return default_coefficient

    if HARDCODED_COEFFICIENTS.get(tournament_id):
        return HARDCODED_COEFFICIENTS.get(tournament_id).get(player.id, 0)

    return default_coefficient
