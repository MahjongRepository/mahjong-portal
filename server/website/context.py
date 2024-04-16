# -*- coding: utf-8 -*-

from django.conf import settings
from django.utils import timezone
from django.utils.translation import get_language


def context(request):
    language = get_language()

    return {
        "SCHEME": settings.SCHEME,
        "SHORT_DATE_FORMAT": language == "ru" and "d.m.Y" or "Y-m-d",
        "CURRENT_YEAR": timezone.now().year,
    }
