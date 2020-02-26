from rating.calculation.rr import RatingRRCalculation
from tournament.models import Tournament


class RatingCRRCalculation(RatingRRCalculation):
    TOURNAMENT_TYPES = [Tournament.CRR, Tournament.RR, Tournament.EMA, Tournament.FOREIGN_EMA]
