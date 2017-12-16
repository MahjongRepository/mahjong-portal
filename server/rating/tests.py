from django.test import TestCase
from django.utils import timezone

from player.models import Player
from rating.calculation.inner import InnerRatingCalculation
from settings.models import Country, TournamentType
from tournament.models import Tournament, TournamentResult


class InnerRatingTestCase(TestCase):

    def setUp(self):
        self.country = Country.objects.create(code='ru', name='Russia')
        self.player = Player.objects.create(first_name='test', last_name='test', country=self.country)

    def _create_tournament(self, players=1, session=1):
        return Tournament.objects.create(
            name='test',
            date=timezone.now(),
            country=self.country,
            tournament_type=TournamentType.objects.create(name='ema'),
            number_of_players=players,
            number_of_sessions=session
        )

    def _create_tournament_result(self, tournament, place):
        return TournamentResult.objects.create(
            place=place,
            tournament=tournament,
            player=self.player
        )

    def test_tournament_coefficient_and_number_of_players(self):
        calculator = InnerRatingCalculation()
        tournament = self._create_tournament(players=16, session=4)

        self.assertEqual(calculator.calculate_tournament_coefficient(tournament), 1)

        tournament = self._create_tournament(players=40, session=4)

        self.assertEqual(calculator.calculate_tournament_coefficient(tournament), 1.1)

        tournament = self._create_tournament(players=60, session=4)

        self.assertEqual(calculator.calculate_tournament_coefficient(tournament), 1.2)

        tournament = self._create_tournament(players=80, session=4)

        self.assertEqual(calculator.calculate_tournament_coefficient(tournament), 1.3)

    def test_tournament_coefficient_and_number_of_sessions(self):
        calculator = InnerRatingCalculation()
        tournament = self._create_tournament(players=16, session=4)

        self.assertEqual(calculator.calculate_tournament_coefficient(tournament), 1)

        tournament = self._create_tournament(players=16, session=8)

        self.assertEqual(calculator.calculate_tournament_coefficient(tournament), 1.05)

        tournament = self._create_tournament(players=16, session=10)

        self.assertEqual(calculator.calculate_tournament_coefficient(tournament), 1.07)

        tournament = self._create_tournament(players=16, session=12)

        self.assertEqual(calculator.calculate_tournament_coefficient(tournament), 1.1)

    def test_calculate_player_base_rank(self):
        calculator = InnerRatingCalculation()
        tournament = self._create_tournament(players=80, session=4)

        result = self._create_tournament_result(tournament, place=1)
        self.assertEqual(calculator.calculate_base_rank(result), 1000)

        result = self._create_tournament_result(tournament, place=80)
        self.assertEqual(calculator.calculate_base_rank(result), 0)

        result = self._create_tournament_result(tournament, place=40)
        self.assertEqual(calculator.calculate_base_rank(result), 506)

    def test_calculate_rating_delta(self):
        calculator = InnerRatingCalculation()
        tournament = self._create_tournament(players=80, session=12)

        result = self._create_tournament_result(tournament, place=40)
        # 506 * 1.4
        self.assertEqual(calculator.calculate_rating_delta(result), 708)
