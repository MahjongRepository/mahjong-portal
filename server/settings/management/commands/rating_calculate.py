from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from rating.calculation.crr import RatingCRRCalculation
from rating.calculation.ema import EmaRatingCalculation
from rating.calculation.rr import RatingRRCalculation
from rating.models import Rating, RatingDelta, RatingResult
from settings.models import TournamentType
from tournament.models import Tournament


def get_date_string():
    return timezone.now().strftime('%H:%M:%S')


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('rating_type', type=str)
        parser.add_argument('--tournament_id', type=int)

    def handle(self, *args, **options):
        print('{0}: Start'.format(get_date_string()))

        allowed_ratings = ['rr', 'crr', 'ema']
        rating_type = options['rating_type']

        if rating_type not in allowed_ratings:
            print('Unknown rating type: {}'.format(rating_type))
            return

        rating = None
        tournaments = None
        calculator = None

        if rating_type == 'rr':
            calculator = RatingRRCalculation()
            rating = Rating.objects.get(type=Rating.RR)
            tournaments = Tournament.objects.all().order_by('end_date')

        if rating_type == 'crr':
            calculator = RatingCRRCalculation()
            rating = Rating.objects.get(type=Rating.CRR)
            tournaments = Tournament.objects.all().order_by('end_date')

        if rating_type == 'ema':
            calculator = EmaRatingCalculation()
            rating = Rating.objects.get(type=Rating.EMA)
            tournaments = (Tournament.objects
                                     .filter(Q(tournament_type__slug=TournamentType.EMA) | Q(tournament_type__slug=TournamentType.FOREIGN_EMA))
                                     .order_by('end_date'))

        erase_scores = True

        if options['tournament_id']:
            erase_scores = False
            tournaments = Tournament.objects.filter(id=options['tournament_id'])

        with transaction.atomic():
            if erase_scores:
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
