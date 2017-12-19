from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db.models import Sum
from django.utils import timezone

from player.models import Player
from rating.calculation.inner import InnerRatingCalculation
from rating.models import Rating, RatingDelta
from tournament.models import Tournament, TournamentResult





def get_date_string():
    return timezone.now().strftime('%H:%M:%S')


class Command(BaseCommand):

    def handle(self, *args, **options):
        print('{0}: Start'.format(get_date_string()))

        rating = Rating.objects.get(type=Rating.INNER)

        RatingDelta.objects.filter(rating=rating).delete()
        Player.objects.all().update(inner_rating_place=None)
        Player.objects.all().update(inner_rating_score=None)

        calculator = InnerRatingCalculation()

        tournaments = Tournament.objects.all().order_by('date')

        processed = 1
        total = tournaments.count()
        for tournament in tournaments:
            print('Process {}/{}'.format(processed, total))

            calculator.calculate_players_deltas(tournament, rating)

            processed += 1

        print('{0}: End'.format(get_date_string()))
