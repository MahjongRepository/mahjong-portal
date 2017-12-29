from django.test import TestCase
from django.utils import timezone

from player.models import Player
from rating.calculation.inner import InnerRatingCalculation
from rating.mixins import RatingTestMixin
from rating.models import Rating, RatingDelta, RatingResult
from settings.models import Country, TournamentType
from tournament.models import Tournament, TournamentResult


class InnerRatingTestCase(TestCase, RatingTestMixin):

    def setUp(self):
        self.set_up_initial_objects()

    def test_tournament_coefficient_and_number_of_players(self):
        calculator = InnerRatingCalculation()

        tournament = self.create_tournament(players=0, sessions=8)
        self.assertEqual(calculator.calculate_tournament_coefficient(tournament), 1)

        tournament = self.create_tournament(players=16, sessions=8)
        self.assertEqual(calculator.calculate_tournament_coefficient(tournament), 0.8)

        tournament = self.create_tournament(players=24, sessions=8)
        self.assertEqual(calculator.calculate_tournament_coefficient(tournament), 1)

        tournament = self.create_tournament(players=40, sessions=8)
        self.assertEqual(calculator.calculate_tournament_coefficient(tournament), 1.1)

        tournament = self.create_tournament(players=80, sessions=8)
        self.assertEqual(calculator.calculate_tournament_coefficient(tournament), 1.2)

    def test_tournament_coefficient_and_number_of_sessions(self):
        calculator = InnerRatingCalculation()

        tournament = self.create_tournament(players=24, sessions=0)
        self.assertEqual(calculator.calculate_tournament_coefficient(tournament), 1)

        tournament = self.create_tournament(players=24, sessions=4)
        self.assertEqual(calculator.calculate_tournament_coefficient(tournament), 0.8)

        tournament = self.create_tournament(players=24, sessions=8)
        self.assertEqual(calculator.calculate_tournament_coefficient(tournament), 1)

        tournament = self.create_tournament(players=24, sessions=10)
        self.assertEqual(calculator.calculate_tournament_coefficient(tournament), 1.1)

        tournament = self.create_tournament(players=24, sessions=12)
        self.assertEqual(calculator.calculate_tournament_coefficient(tournament), 1.3)

    def test_calculate_player_base_rank(self):
        calculator = InnerRatingCalculation()
        tournament = self.create_tournament(players=80, sessions=4)

        result = self.create_tournament_result(tournament, place=1)
        self.assertEqual(calculator.calculate_base_rank(result), 1000)

        result = self.create_tournament_result(tournament, place=20)
        self.assertEqual(calculator.calculate_base_rank(result), 513)

        result = self.create_tournament_result(tournament, place=40)
        self.assertEqual(calculator.calculate_base_rank(result), 0)

        result = self.create_tournament_result(tournament, place=60)
        self.assertEqual(calculator.calculate_base_rank(result), -513)

        result = self.create_tournament_result(tournament, place=80)
        self.assertEqual(calculator.calculate_base_rank(result), -1000)

    def test_calculate_rating_delta(self):
        calculator = InnerRatingCalculation()
        tournament = self.create_tournament(players=80, sessions=12)

        result = self.create_tournament_result(tournament, place=20)
        base_rank = calculator.calculate_base_rank(result)
        coefficient = calculator.calculate_tournament_coefficient(tournament)
        self.assertEqual(calculator.calculate_rating_delta(result), round(base_rank * coefficient))

    def test_calculate_player_positions_changes(self):
        calculator = InnerRatingCalculation()
        rating, _ = Rating.objects.get_or_create(type=Rating.INNER)

        first_player = self.create_player()
        second_player = self.create_player()

        # First tournament

        tournament = self.create_tournament(players=4, sessions=2)
        self.create_tournament_result(tournament, place=1, player=first_player)
        self.create_tournament_result(tournament, place=2, player=second_player)

        calculator.calculate_players_deltas(tournament, rating)

        self.assertEqual(RatingResult.objects.get(player=first_player).place, 1)
        self.assertEqual(RatingResult.objects.get(player=second_player).place, 2)

        # Second tournament

        tournament = self.create_tournament(players=4, sessions=2)
        self.create_tournament_result(tournament, place=4, player=first_player)
        self.create_tournament_result(tournament, place=1, player=second_player)

        calculator.calculate_players_deltas(tournament, rating)

        self.assertEqual(RatingResult.objects.get(player=first_player).place, 2)
        self.assertEqual(RatingResult.objects.get(player=second_player).place, 1)
