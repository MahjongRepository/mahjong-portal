from django.conf import settings
from django.utils.translation import get_language


def context(request):
    language = get_language()

    return {
        'YANDEX_METRIKA_ID': settings.YANDEX_METRIKA_ID,
        'GOOGLE_VERIFICATION_CODE': settings.GOOGLE_VERIFICATION_CODE,
        'YANDEX_VERIFICATION_CODE': settings.YANDEX_VERIFICATION_CODE,
        'APP_VERSION': settings.APP_VERSION,
        'SCHEME': settings.SCHEME,
        'SHORT_DATE_FORMAT': language == 'ru' and 'd.m.Y' or 'd/m/Y'
    }
