import datetime

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from rating.calculation.crr import RatingCRRCalculation
from rating.calculation.online import RatingOnlineCalculation
from rating.calculation.rr import RatingRRCalculation
from rating.models import Rating, RatingDelta, RatingResult
from tournament.models import Tournament


def get_date_string():
    return timezone.now().strftime('%H:%M:%S')


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('rating_type', type=str)

    def handle(self, *args, **options):
        print('{0}: Start'.format(get_date_string()))

        rating_type = options['rating_type']
        rating = None
        tournaments = None
        calculator = None
        rating_date = None
        today = datetime.datetime.now().date()

        if rating_type == 'rr':
            rating_date = today - datetime.timedelta(days=365 * 2)

            calculator = RatingRRCalculation()
            rating = Rating.objects.get(type=Rating.RR)
            tournaments = Tournament.public.filter(
                Q(tournament_type=Tournament.RR) |
                Q(tournament_type=Tournament.EMA) |
                Q(tournament_type=Tournament.FOREIGN_EMA)
            ).filter(is_upcoming=False).order_by('end_date')

        if rating_type == 'crr':
            rating_date = today - datetime.timedelta(days=365 * 2)

            calculator = RatingCRRCalculation()
            rating = Rating.objects.get(type=Rating.CRR)
            tournaments = Tournament.public.filter(
                Q(tournament_type=Tournament.CRR) |
                Q(tournament_type=Tournament.RR) |
                Q(tournament_type=Tournament.EMA) |
                Q(tournament_type=Tournament.FOREIGN_EMA)
            ).filter(is_upcoming=False).order_by('end_date')

        if rating_type == 'online':
            rating_date = today - datetime.timedelta(days=913)

            calculator = RatingOnlineCalculation()
            rating = Rating.objects.get(type=Rating.ONLINE)
            tournaments = (Tournament.public
                           .filter(tournament_type=Tournament.ONLINE)
                           .filter(is_upcoming=False)
                           .order_by('end_date'))

        if not rating:
            print('Unknown rating type: {}'.format(rating_type))
            return

        print('Calculating dates...')

        continue_work = True

        with transaction.atomic():
            RatingResult.objects.filter(rating=rating).delete()
            RatingDelta.objects.filter(rating=rating).delete()

            tournaments_diff = {}
            dates_to_process = []
            while continue_work:
                need_to_recalculate = False

                # we need to rebuild rating only after changes in tournaments
                # there is no need to rebuild it each day
                limited_tournaments = tournaments.filter(end_date__lte=rating_date)
                for tournament in limited_tournaments:
                    if tournament.id not in tournaments_diff:
                        # new tournament was added
                        need_to_recalculate = True
                        tournaments_diff[tournament.id] = 100
                    else:
                        # old tournament changed age weight
                        age = calculator.tournament_age(tournament.end_date, rating_date)
                        if tournaments_diff[tournament.id] != age:
                            need_to_recalculate = True
                            tournaments_diff[tournament.id] = age

                if need_to_recalculate:
                    dates_to_process.append(rating_date)

                rating_date = rating_date + datetime.timedelta(days=1)

                if rating_date > today:
                    continue_work = False

            print('Dates to process: {}'.format(len(dates_to_process)))

            self.calculate_rating(
                dates_to_process,
                tournaments,
                calculator,
                rating,
                calculate_last_date=True
            )

            important_dates = [
                # ERMC 2019 qualification date
                datetime.date(2019, 1, 1),
                # WRC 2020 qualification date
                datetime.date(2020, 1, 1),
                # WRC 2020 second qualification date
                datetime.date(2020, 3, 1),
                # just a date
                datetime.date(2021, 1, 1),
            ]

            self.calculate_rating(
                important_dates,
                tournaments,
                calculator,
                rating,
                calculate_last_date=False
            )

        print('{0}: End'.format(get_date_string()))

    def calculate_rating(self, dates_to_process, tournaments, calculator, rating, calculate_last_date=True):
        for i, rating_date in enumerate(dates_to_process):
            if calculate_last_date:
                is_last = i == len(dates_to_process) - 1
            else:
                is_last = False

            limited_tournaments = tournaments.filter(end_date__lte=rating_date)

            print(rating_date, limited_tournaments.count(), is_last)

            for tournament in limited_tournaments:
                calculator.calculate_players_deltas(tournament, rating, rating_date, is_last)

            calculator.calculate_players_rating_rank(rating, rating_date, is_last)
