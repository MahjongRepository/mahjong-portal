import string
import random


def make_random_letters_and_digit_string(length=15):
    random_chars = string.ascii_lowercase + string.digits
    return ''.join(random.choice(random_chars) for _ in range(length))


def transliterate_name(russian_name):
    """
    Russian name to English letters
    with official government transliteration table
    :return:
    """

    table = {
        'а': 'a',
        'б': 'b',
        'в': 'v',
        'г': 'g',
        'д': 'd',
        'е': 'e',
        'ё': 'e',
        'ж': 'zh',
        'з': 'z',
        'и': 'i',
        'й': 'i',
        'к': 'k',
        'л': 'l',
        'м': 'm',
        'н': 'n',
        'о': 'о',
        'п': 'p',
        'р': 'r',
        'с': 's',
        'т': 't',
        'у': 'u',
        'ф': 'f',
        'х': 'kh',
        'ц': 'ts',
        'ч': 'ch',
        'ш': 'sh',
        'щ': 'shch',
        'ъ': 'ie',
        'ь': '',
        'ы': 'y',
        'э': 'e',
        'ю': 'iu',
        'я': 'ia'
    }

    transliterated = ''
    for letter in russian_name.lower():
        if letter in table:
            transliterated += table[letter]
        else:
            transliterated += letter

    return transliterated.title()
