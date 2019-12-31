from datetime import datetime

from django.core.management import BaseCommand, call_command
from django.utils import timezone

from player.models import Player
from rating.models import Rating
from settings.models import Country
from tournament.models import Tournament, TournamentResult


class Command(BaseCommand):

    def handle(self, *args, **options):
        year = timezone.now().year

        country = Country.objects.create(name='Russia', code='RU')
        Rating.objects.create(name='RR', slug='rr', type=Rating.RR)

        first_player = Player.objects.create(
            first_name='Takaharu',
            last_name='Ooi',
            slug='first',
            country=country
        )

        second_player = Player.objects.create(
            first_name='Koshin',
            last_name='Asakura',
            slug='second',
            country=country,
        )

        first_tournament = Tournament.objects.create(
            name='First',
            end_date=datetime(year, 1, 1),
            country=country,
            slug='first',
            number_of_players=2,
            number_of_sessions=20,
            tournament_type=Tournament.RR,
        )

        TournamentResult.objects.create(
            player=first_player, place=1, scores=100000, tournament=first_tournament
        )
        TournamentResult.objects.create(
            player=second_player, place=2, scores=10000, tournament=first_tournament
        )

        second_tournament = Tournament.objects.create(
            name='Second',
            end_date=datetime(year - 1, 9, 10),
            country=country,
            slug='second',
            number_of_players=2,
            number_of_sessions=14,
            tournament_type=Tournament.RR
        )

        TournamentResult.objects.create(
            player=first_player, place=1, scores=100000, tournament=second_tournament
        )
        TournamentResult.objects.create(
            player=second_player, place=2, scores=10000, tournament=second_tournament
        )

        call_command('rating_calculate', 'rr')
