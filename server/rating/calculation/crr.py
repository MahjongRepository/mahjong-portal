from django.db.models import Q

from rating.calculation.rr import RatingRRCalculation
from rating.models import RatingDelta
from tournament.models import Tournament


class RatingCRRCalculation(RatingRRCalculation):

    def get_base_query(self, rating, date):
        base_query = (RatingDelta.objects
                      .filter(rating=rating)
                      .filter(Q(tournament__tournament_type=Tournament.CRR) |
                              Q(tournament__tournament_type=Tournament.RR) |
                              Q(tournament__tournament_type=Tournament.EMA) |
                              Q(tournament__tournament_type=Tournament.FOREIGN_EMA))
                      .filter(tournament__end_date__gte=date))
        return base_query
