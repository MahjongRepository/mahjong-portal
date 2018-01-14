from datetime import datetime

from django.test import TestCase

from rating.calculation.ema import EmaRatingCalculation
from rating.mixins import RatingTestMixin


class EMARatingTestCase(TestCase, RatingTestMixin):

    def setUp(self):
        self.set_up_initial_objects()

    def test_tournament_coefficient_and_number_of_players(self):
        calculator = EmaRatingCalculation()

        tournament = self.create_tournament(players=20)
        self.assertEqual(calculator.players_coefficient(tournament), 0)

        tournament = self.create_tournament(players=40)
        self.assertEqual(calculator.players_coefficient(tournament), 0)

        tournament = self.create_tournament(players=41)
        self.assertEqual(calculator.players_coefficient(tournament), 0.5)

        tournament = self.create_tournament(players=80)
        self.assertEqual(calculator.players_coefficient(tournament), 0.5)

        tournament = self.create_tournament(players=81)
        self.assertEqual(calculator.players_coefficient(tournament), 1)

        tournament = self.create_tournament(players=150)
        self.assertEqual(calculator.players_coefficient(tournament), 1)

    def test_tournament_coefficient_and_duration(self):
        calculator = EmaRatingCalculation()

        start_date = datetime(2017, 10, 10)
        end_date = datetime(2017, 10, 10)

        tournament = self.create_tournament(start_date=start_date, end_date=end_date)
        self.assertEqual(calculator.duration_coefficient(tournament), 1)

        end_date = datetime(2017, 10, 11)
        tournament = self.create_tournament(start_date=start_date, end_date=end_date)
        self.assertEqual(calculator.duration_coefficient(tournament), 2)

        end_date = datetime(2017, 10, 12)
        tournament = self.create_tournament(start_date=start_date, end_date=end_date)
        self.assertEqual(calculator.duration_coefficient(tournament), 3)

        end_date = datetime(2017, 10, 14)
        tournament = self.create_tournament(start_date=start_date, end_date=end_date)
        self.assertEqual(calculator.duration_coefficient(tournament), 3)

    def test_tournament_coefficient_and_countries(self):
        calculator = EmaRatingCalculation()

        tournament = self.create_tournament()

        self.create_tournament_result(tournament, 1, self.create_player(country_code='1'))
        self.create_tournament_result(tournament, 2, self.create_player(country_code='2'))
        self.create_tournament_result(tournament, 3, self.create_player(country_code='3'))
        self.create_tournament_result(tournament, 4, self.create_player(country_code='4'))
        self.create_tournament_result(tournament, 5, self.create_player(country_code='5'))

        self.assertEqual(calculator.countries_coefficient(tournament), 0)

        self.create_tournament_result(tournament, 6, self.create_player(country_code='6'))

        self.assertEqual(calculator.countries_coefficient(tournament), 0.5)

        self.create_tournament_result(tournament, 7, self.create_player(country_code='7'))
        self.create_tournament_result(tournament, 8, self.create_player(country_code='8'))
        self.create_tournament_result(tournament, 9, self.create_player(country_code='9'))
        self.create_tournament_result(tournament, 10, self.create_player(country_code='10'))

        self.assertEqual(calculator.countries_coefficient(tournament), 0.5)

        self.create_tournament_result(tournament, 11, self.create_player(country_code='11'))

        self.assertEqual(calculator.countries_coefficient(tournament), 1)

    def test_tournament_coefficient_and_qualification(self):
        calculator = EmaRatingCalculation()

        tournament = self.create_tournament(need_qualification=False)
        self.assertEqual(calculator.qualification_coefficient(tournament), 0)

        tournament = self.create_tournament(need_qualification=True)
        self.assertEqual(calculator.qualification_coefficient(tournament), 1)
