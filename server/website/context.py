from django.conf import settings


def context(request):

    return {
        'YANDEX_METRIKA_ID': settings.YANDEX_METRIKA_ID,
        'GOOGLE_VERIFICATION_CODE': settings.GOOGLE_VERIFICATION_CODE,
        'YANDEX_VERIFICATION_CODE': settings.YANDEX_VERIFICATION_CODE,
        'APP_VERSION': settings.APP_VERSION,
        'SCHEME': settings.SCHEME
    }
