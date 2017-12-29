import string
import random


def make_random_letters_and_digit_string(length=15):
    random_chars = string.ascii_lowercase + string.digits
    return ''.join(random.choice(random_chars) for _ in range(length))


transliteration_table = {
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
    'о': 'o',
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
    'щ': 'shh',
    'ъ': 'ie',
    'ь': '',
    'ы': 'y',
    'э': 'e',
    'ю': 'yu',
    'я': 'ya'
}


def transliterate_name(russian_name):
    """
    Russian name to English letters
    with official government transliteration table
    :return:
    """
    transliterated = ''
    for letter in russian_name.lower():
        if letter in transliteration_table:
            transliterated += transliteration_table[letter]
        else:
            transliterated += letter

    return transliterated.title()
