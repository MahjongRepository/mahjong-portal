from django.conf import settings
from django.utils import timezone
from django.utils.translation import get_language


def context(request):
    language = get_language()

    return {
        'GOOGLE_VERIFICATION_CODE': settings.GOOGLE_VERIFICATION_CODE,
        'YANDEX_VERIFICATION_CODE': settings.YANDEX_VERIFICATION_CODE,
        'SCHEME': settings.SCHEME,
        'SHORT_DATE_FORMAT': language == 'ru' and 'd.m.Y' or 'd/m/Y',
        'CURRENT_YEAR': timezone.now().year
    }
