from django.conf import settings


def context(request):

    return {
        'YANDEX_METRIKA_ID': settings.YANDEX_METRIKA_ID,
    }
