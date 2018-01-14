from rating.calculation.rr import RatingRRCalculation


class RatingCRRCalculation(RatingRRCalculation):
    MIN_PLAYERS_REQUIREMENTS = 12
    HAS_ACCREDITATION = False
