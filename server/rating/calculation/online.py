from datetime import timedelta

from dateutil.relativedelta import relativedelta
from django.db.models import Q

from player.models import Player
from rating.calculation.rr import RatingRRCalculation
from rating.models import RatingDelta
from tournament.models import Tournament, TournamentResult


class RatingOnlineCalculation(RatingRRCalculation):
    MIN_TOURNAMENTS_NUMBER = 1
    FIRST_PART_MIN_TOURNAMENTS = 5
    SECOND_PART_MIN_TOURNAMENTS = 3

    def get_base_query(self, rating, start_date, rating_date):
        base_query = (
            RatingDelta.objects.filter(rating=rating)
            .filter(tournament__tournament_type=Tournament.ONLINE)
            .filter(
                Q(tournament__end_date__gt=start_date)
                & Q(tournament__end_date__lte=rating_date)
            )
            .filter(date=rating_date)
        )
        return base_query

    def get_players(self):
        player_ids = TournamentResult.objects.filter(
            tournament__tournament_type=Tournament.ONLINE
        ).values_list("player_id", flat=True)
        return (
            Player.objects.filter(id__in=player_ids)
            .exclude(is_replacement=True)
            .exclude(is_hide=True)
        )

    def tournament_age(self, end_date, rating_date):
        diff = relativedelta(rating_date, end_date)

        if diff.years < 1:
            return 100
        elif diff.years < 2 and diff.months < 6:
            return 75
        elif diff.years < 2 and diff.months >= 6:
            return 50
        elif diff.years < 3 and diff.months < 6:
            return 25
        else:
            return 0

    def get_date(self, rating_date):
        # two and half years ago
        return rating_date - timedelta(days=913)
