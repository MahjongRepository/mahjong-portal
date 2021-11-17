from datetime import datetime

from django.http import Http404
from django.utils import timezone

from rating.models import RatingResult


def get_latest_rating_date(rating):
    today = timezone.now().date()
    rating_results = RatingResult.objects.filter(rating=rating).filter(date__lte=today).order_by("date")
    return today, rating_results.last().date


def parse_rating_date(year, month, day):
    is_last = True
    rating_date = None
    today = None
    if year and month and day:
        try:
            rating_date = datetime(int(year), int(month), int(day)).date()
            today = rating_date
            is_last = False
        except ValueError:
            raise Http404 from None

    return today, rating_date, is_last
