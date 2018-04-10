from datetime import timedelta

from dateutil.relativedelta import relativedelta
from django.utils import timezone

from player.models import Player
from rating.calculation.rr import RatingRRCalculation
from rating.models import RatingDelta
from tournament.models import Tournament


class RatingOnlineCalculation(RatingRRCalculation):
    MIN_TOURNAMENTS_NUMBER = 1
    FIRST_PART_MIN_TOURNAMENTS = 5
    SECOND_PART_MIN_TOURNAMENTS = 3

    def get_base_query(self, rating, date):
        base_query = (RatingDelta.objects
                      .filter(rating=rating)
                      .filter(tournament__tournament_type=Tournament.ONLINE)
                      .filter(tournament__end_date__gte=date))
        return base_query

    def get_players(self):
        return Player.objects.all()

    def tournament_age(self, tournament):
        today = timezone.now().date()
        end_date = tournament.end_date
        diff = relativedelta(today, end_date)
        months = diff.years * 12 + diff.months + diff.days / 30

        if months <= 12:
            return 100
        elif 12 < months <= 18:
            return 75
        elif 18 < months <= 24:
            return 50
        elif 24 < months <= 30:
            return 25
        else:
            return 0

    def get_date(self):
        # two and half years ago
        return timezone.now().date() - timedelta(days=913)
