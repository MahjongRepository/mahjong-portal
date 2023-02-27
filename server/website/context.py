from django.conf import settings
from django.utils import timezone
from django.utils.translation import get_language


def context(request):
    language = get_language()

    return {
        "SCHEME": settings.SCHEME,
        "UNAMI_ID": settings.UNAMI_ID,
        "UNAMI_DOMAIN": settings.UNAMI_DOMAIN,
        "SHORT_DATE_FORMAT": language == "ru" and "d.m.Y" or "Y-m-d",
        "CURRENT_YEAR": timezone.now().year,
    }
