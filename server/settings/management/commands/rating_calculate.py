from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from rating.calculation.crr import RatingCRRCalculation
from rating.calculation.ema import EmaRatingCalculation
from rating.calculation.rr import RatingRRCalculation
from rating.models import Rating, RatingDelta, RatingResult
from tournament.models import Tournament


def get_date_string():
    return timezone.now().strftime('%H:%M:%S')


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('rating_type', type=str)

    def handle(self, *args, **options):
        print('{0}: Start'.format(get_date_string()))

        rating_type = options['rating_type']
        rating = None
        tournaments = None
        calculator = None

        if rating_type == 'rr':
            calculator = RatingRRCalculation()
            rating = Rating.objects.get(type=Rating.RR)
            tournaments = Tournament.objects.filter(
                Q(tournament_type=Tournament.RR) |
                Q(tournament_type=Tournament.EMA) |
                Q(tournament_type=Tournament.FOREIGN_EMA)
            ).order_by('end_date')

        if rating_type == 'crr':
            calculator = RatingCRRCalculation()
            rating = Rating.objects.get(type=Rating.CRR)
            tournaments = Tournament.objects.filter(
                Q(tournament_type=Tournament.CRR) |
                Q(tournament_type=Tournament.RR) |
                Q(tournament_type=Tournament.EMA) |
                Q(tournament_type=Tournament.FOREIGN_EMA)
            ).order_by('end_date')

        if rating_type == 'ema':
            calculator = EmaRatingCalculation()
            rating = Rating.objects.get(type=Rating.EMA)
            tournaments = (Tournament.objects
                           .filter(Q(tournament_type=Tournament.EMA) | Q(tournament_type=Tournament.FOREIGN_EMA))
                           .order_by('end_date'))

        if not rating:
            print('Unknown rating type: {}'.format(rating_type))
            return

        with transaction.atomic():
            RatingDelta.objects.filter(rating=rating).delete()
            RatingResult.objects.filter(rating=rating).delete()

            processed = 1
            total = tournaments.count()
            for tournament in tournaments:
                print('Process {}/{}'.format(processed, total))

                calculator.calculate_players_deltas(tournament, rating)

                processed += 1

            calculator.calculate_players_rating_rank(rating)

        print('{0}: End'.format(get_date_string()))
