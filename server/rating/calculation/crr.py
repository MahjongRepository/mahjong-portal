from rating.calculation.common import RatingDatesMixin
from rating.calculation.rr import RatingRRCalculation
from tournament.models import Tournament


class RatingCRRCalculation(RatingRRCalculation, RatingDatesMixin):
    TOURNAMENT_TYPES = [Tournament.CRR, Tournament.RR, Tournament.EMA, Tournament.FOREIGN_EMA]

    def get_date(self, rating_date):
        return RatingDatesMixin.get_date(self, rating_date)

    def tournament_age(self, end_date, rating_date):
        return RatingDatesMixin.tournament_age(self, end_date, rating_date)
