from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from rating.calculation.crr import RatingCRRCalculation
from rating.calculation.ema import EmaRatingCalculation
from rating.calculation.rr import RatingRRCalculation
from rating.models import Rating, RatingDelta, RatingResult
from settings.models import TournamentType
from tournament.models import Tournament, TournamentResult


def get_date_string():
    return timezone.now().strftime('%H:%M:%S')


class Command(BaseCommand):

    def handle(self, *args, **options):
        print('{0}: Start'.format(get_date_string()))

        tournaments = Tournament.objects.all()

        for tournament in tournaments:
            zero_values = TournamentResult.objects.filter(tournament=tournament, scores=None)
            if zero_values.count() > 5:
                print('https://mahjong.click/ru/tournaments/riichi/{}/'.format(tournament.slug))

        print('{0}: End'.format(get_date_string()))
