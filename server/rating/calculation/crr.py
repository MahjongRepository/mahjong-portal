from django.db.models import Q

from rating.calculation.rr import RatingRRCalculation
from rating.models import RatingDelta
from tournament.models import Tournament


class RatingCRRCalculation(RatingRRCalculation):
    def get_base_query(self, rating, start_date, rating_date):
        types = [Tournament.CRR, Tournament.RR, Tournament.EMA, Tournament.FOREIGN_EMA]
        base_query = (
            RatingDelta.objects.filter(rating=rating)
            .filter(tournament__tournament_type__in=types)
            .filter(Q(tournament__end_date__gt=start_date) & Q(tournament__end_date__lte=rating_date))
            .filter(date=rating_date)
        )
        return base_query
