from django.conf import settings


def context(request):

    return {
        'YANDEX_METRIKA_ID': settings.YANDEX_METRIKA_ID,
        'APP_VERSION': settings.APP_VERSION,
        'SCHEME': settings.SCHEME
    }
