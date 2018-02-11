from django.db.models import Q

from player.models import Player
from rating.calculation.rr import RatingRRCalculation
from rating.models import RatingDelta
from tournament.models import Tournament


class RatingOnlineCalculation(RatingRRCalculation):
    MIN_TOURNAMENTS_NUMBER = 1

    def get_base_query(self, rating, date):
        base_query = (RatingDelta.objects
                      .filter(rating=rating)
                      .filter(tournament__tournament_type=Tournament.ONLINE)
                      .filter(tournament__end_date__gte=date))
        return base_query

    def get_players(self):
        return Player.objects.all()
