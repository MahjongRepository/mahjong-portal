import csv
from datetime import timedelta

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

        calculator = InnerRatingCalculation()

        two_years_ago = timezone.now().date() - timedelta(days=365 * 2)

        tournaments = Tournament.objects.filter(end_date__gte=two_years_ago).exclude(tournament_type__slug=TournamentType.FOREIGN_EMA).exclude(is_upcoming=True)

        with open('c.csv', 'w') as f:
            writer = csv.writer(f)
            writer.writerow(['название', 'игроков', 'к. за игроков', 'игр', 'к. за игры', 'к. общий', 'угасание', 'к. с угасанием'])

            for tournament in tournaments:
                writer.writerow([
                    tournament.name_ru,
                    tournament.number_of_players,
                    calculator.players_coefficient(tournament),
                    tournament.number_of_sessions,
                    calculator.sessions_coefficient(tournament),
                    calculator.tournament_coefficient(tournament),
                    calculator.tournament_age(tournament),
                    calculator._calculate_percentage(calculator.tournament_coefficient(tournament), calculator.tournament_age(tournament)),
                ])

        print('{0}: End'.format(get_date_string()))
