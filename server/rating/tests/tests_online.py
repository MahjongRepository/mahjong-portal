from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from rating.calculation.online import RatingOnlineCalculation
from rating.mixins import RatingTestMixin


class InnerRatingTestCase(TestCase, RatingTestMixin):
    def setUp(self):
        self.set_up_initial_objects()

    def test_calculate_age_weight_of_tournament(self):
        calculator = RatingOnlineCalculation()

        now = timezone.now().date()

        tournament = self.create_tournament(end_date=now)
        self.assertEqual(calculator.tournament_age(tournament.end_date, now), 100)

        tournament = self.create_tournament(end_date=now - timedelta(days=60))
        self.assertEqual(calculator.tournament_age(tournament.end_date, now), 100)

        tournament = self.create_tournament(end_date=now - timedelta(days=364))
        self.assertEqual(calculator.tournament_age(tournament.end_date, now), 100)

        tournament = self.create_tournament(end_date=now - timedelta(days=365))
        self.assertEqual(calculator.tournament_age(tournament.end_date, now), 75)

        tournament = self.create_tournament(end_date=now - timedelta(days=365 + 31))
        self.assertEqual(calculator.tournament_age(tournament.end_date, now), 75)

        tournament = self.create_tournament(end_date=now - timedelta(days=365 + 7 * 31))
        self.assertEqual(calculator.tournament_age(tournament.end_date, now), 50)

        tournament = self.create_tournament(end_date=now - timedelta(days=365 * 2 - 1))
        self.assertEqual(calculator.tournament_age(tournament.end_date, now), 50)

        tournament = self.create_tournament(end_date=now - timedelta(days=365 * 2))
        self.assertEqual(calculator.tournament_age(tournament.end_date, now), 25)

        tournament = self.create_tournament(end_date=now - timedelta(days=365 * 2 + 180))
        self.assertEqual(calculator.tournament_age(tournament.end_date, now), 25)

        tournament = self.create_tournament(end_date=now - timedelta(days=365 * 2 + 185))
        self.assertEqual(calculator.tournament_age(tournament.end_date, now), 0)
