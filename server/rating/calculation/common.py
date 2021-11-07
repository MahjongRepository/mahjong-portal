from datetime import timedelta

from dateutil.relativedelta import relativedelta


class RatingDatesMixin:
    def get_date(self, rating_date):
        # two years ago
        return rating_date - timedelta(days=365 * 2)

    def tournament_age(self, end_date, rating_date):
        """
        Check about page for detailed description
        """

        diff = relativedelta(rating_date, end_date)
        part = (1 / 7) * 100

        if diff.years < 1:
            return 100
        elif 1 <= diff.years < 2:
            value = int(diff.months / 2 + 1)
            return round(100 - (value * part), 2)
        else:
            return 0
