import datetime

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from rating.calculation.crr import RatingCRRCalculation
from rating.calculation.ema import RatingEMACalculation
from rating.calculation.online import RatingOnlineCalculation
from rating.calculation.rr import RatingRRCalculation
from rating.models import Rating, RatingDelta, RatingResult, RatingDate
from tournament.models import Tournament


def get_date_string():
    return timezone.now().strftime('%H:%M:%S')


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('rating_type', type=str)

    def handle(self, *args, **options):
        print('{0}: Start'.format(get_date_string()))

        rating_type = options['rating_type']

        today = datetime.datetime.now().date()

        rating_options = {
            'rr': {
                'rating_date': today - datetime.timedelta(days=365 * 2),
                'calculator': RatingRRCalculation,
                'rating_type': Rating.RR,
                'tournament_types': [Tournament.RR, Tournament.EMA, Tournament.FOREIGN_EMA],
            },
            'crr': {
                'rating_date': today - datetime.timedelta(days=365 * 2),
                'calculator': RatingCRRCalculation,
                'rating_type': Rating.CRR,
                'tournament_types': [Tournament.CRR, Tournament.RR, Tournament.EMA, Tournament.FOREIGN_EMA],
            },
            'online': {
                'rating_date': today - datetime.timedelta(days=913),
                'calculator': RatingOnlineCalculation,
                'rating_type': Rating.ONLINE,
                'tournament_types': [Tournament.ONLINE],
            },
            'ema': {
                'rating_date': today - datetime.timedelta(days=365 * 2),
                'calculator': RatingEMACalculation,
                'rating_type': Rating.EMA,
                'tournament_types': [Tournament.EMA, Tournament.FOREIGN_EMA, Tournament.CHAMPIONSHIP],
            },
        }

        rating_data = rating_options.get(rating_type)
        if not rating_data:
            print('Unknown rating type: {}'.format(rating_type))
            return

        calculator = rating_data['calculator']()
        rating_date = rating_data['rating_date']
        rating = Rating.objects.get(type=rating_data['rating_type'])
        tournaments = (Tournament.public
                       .filter(tournament_type__in=rating_data['tournament_types'])
                       .filter(is_upcoming=False)
                       .order_by('end_date'))

        print('Calculating dates...')

        with transaction.atomic():
            dates_to_process, rating_date = self.find_tournament_dates_changes(
                rating_date,
                today,
                tournaments,
                calculator
            )

            important_dates = [
                # ERMC 2019 qualification date
                datetime.date(2019, 1, 1),
            ]

            dates_to_process = dates_to_process + important_dates
            # make sure that all dates are unique
            dates_to_process = sorted(list(set(dates_to_process)))

            print('Found dates: {}'.format(len(dates_to_process)))

            already_added_dates = RatingDate.objects.filter(rating=rating).values_list('date', flat=True)
            dates_to_recalculate = sorted(list(set(dates_to_process) - set(already_added_dates)))

            print('Dates to recalculate: {}'.format(len(dates_to_recalculate)))

            self.calculate_rating(
                dates_to_recalculate,
                tournaments,
                calculator,
                rating
            )

            print('')
            print('Calculating future dates...')

            future_dates = [
                datetime.date(2020, 1, 1),
                # WRC 2020 qualification date
                datetime.date(2020, 2, 1),
            ]

            first_future_date = future_dates[0]
            latest_future_date = future_dates[-1]

            RatingDate.objects.filter(
                rating=rating, date__gte=first_future_date
            ).delete()
            RatingResult.objects.filter(
                rating=rating, date__gte=first_future_date
            ).delete()
            RatingDelta.objects.filter(
                rating=rating, date__gte=first_future_date
            ).delete()

            dates_to_process, _ = self.find_tournament_dates_changes(
                rating_date,
                latest_future_date,
                tournaments,
                calculator
            )

            dates_to_recalculate = sorted(list(set(dates_to_process + future_dates)))
            print('Dates to process: {}'.format(len(dates_to_recalculate)))

            self.calculate_rating(
                dates_to_recalculate,
                tournaments,
                calculator,
                rating,
                is_future=True
            )

        print('{0}: End'.format(get_date_string()))

    def calculate_rating(self, dates_to_process, tournaments, calculator, rating, is_future=False):
        for i, rating_date in enumerate(dates_to_process):
            RatingDate.objects.create(rating=rating, date=rating_date, is_future=is_future)

            RatingResult.objects.filter(
                rating=rating,
                date=rating_date
            ).delete()
            RatingDelta.objects.filter(
                rating=rating,
                date=rating_date
            ).delete()

            limited_tournaments = tournaments.filter(end_date__lte=rating_date)

            print(rating_date, limited_tournaments.count())

            for tournament in limited_tournaments:
                calculator.calculate_players_deltas(tournament, rating, rating_date)

            calculator.calculate_players_rating_rank(rating, rating_date)

    def find_tournament_dates_changes(self, start_date, stop_date, tournaments, calculator):
        continue_work = True
        tournaments_diff = {}
        dates_to_process = []
        while continue_work:
            need_to_recalculate = False

            # we need to rebuild rating only after changes in tournaments
            # there is no need to rebuild it each day
            limited_tournaments = tournaments.filter(end_date__lte=start_date)
            for tournament in limited_tournaments:
                if tournament.id not in tournaments_diff:
                    age = calculator.tournament_age(tournament.end_date, start_date)
                    need_to_recalculate = True
                    tournaments_diff[tournament.id] = age
                else:
                    # old tournament changed age weight
                    age = calculator.tournament_age(tournament.end_date, start_date)
                    if tournaments_diff[tournament.id] != age:
                        need_to_recalculate = True
                        tournaments_diff[tournament.id] = age

            if need_to_recalculate:
                dates_to_process.append(start_date)

            start_date = start_date + datetime.timedelta(days=1)

            if start_date > stop_date:
                continue_work = False

        return dates_to_process, start_date
