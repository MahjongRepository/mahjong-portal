from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from player.models import Player
from rating.calculation.inner import InnerRatingCalculation
from rating.models import Rating, RatingDelta, RatingResult
from settings.models import TournamentType
from tournament.models import Tournament


def get_date_string():
    return timezone.now().strftime('%H:%M:%S')


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--tournament_id', type=int)

    def handle(self, *args, **options):
        print('{0}: Start'.format(get_date_string()))

        erase_scores = True

        rating = Rating.objects.get(type=Rating.INNER)
        if options['tournament_id']:
            erase_scores = False
            tournaments = Tournament.objects.filter(id=options['tournament_id']).order_by('end_date')
        else:
            tournaments = Tournament.objects.all().order_by('end_date')

        with transaction.atomic():
            if erase_scores:
                RatingDelta.objects.filter(rating=rating).delete()
                RatingResult.objects.filter(rating=rating).delete()

            calculator = InnerRatingCalculation()

            processed = 1
            total = tournaments.count()
            for tournament in tournaments:
                print('Process {}/{}'.format(processed, total))

                calculator.calculate_players_deltas(tournament, rating)

                processed += 1

            calculator.calculate_players_rating_rank(rating)

        print('{0}: End'.format(get_date_string()))
