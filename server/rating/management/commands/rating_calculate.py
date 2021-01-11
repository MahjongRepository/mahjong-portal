import datetime

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from rating.calculation.crr import RatingCRRCalculation
from rating.calculation.ema import RatingEMACalculation
from rating.calculation.online import RatingOnlineCalculation
from rating.calculation.rr import RatingRRCalculation
from rating.models import Rating, RatingDate, RatingDelta, RatingResult
from tournament.models import Tournament, TournamentResult


def get_date_string():
    return timezone.now().strftime("%H:%M:%S")


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("rating_type", type=str)
        parser.add_argument("--date", type=str)
        parser.add_argument("--from-zero", type=bool, default=False)

    def handle(self, *args, **options):
        print("{0}: Start".format(get_date_string()))

        rating_type = options["rating_type"]
        specified_date = options["date"]
        from_zero = options["from_zero"]

        tournaments_diff = {}
        today = datetime.datetime.now().date()

        rating_options = {
            "rr": {"calculator": RatingRRCalculation, "rating_type": Rating.RR},
            "crr": {"calculator": RatingCRRCalculation, "rating_type": Rating.CRR},
            "online": {"calculator": RatingOnlineCalculation, "rating_type": Rating.ONLINE},
            "ema": {"calculator": RatingEMACalculation, "rating_type": Rating.EMA},
        }

        rating_data = rating_options.get(rating_type)
        if not rating_data:
            print("Unknown rating type: {}".format(rating_type))
            return

        print('Calculating "{}" rating...'.format(rating_type.upper()))

        calculator = rating_data["calculator"]()
        rating_date = calculator.get_date(today)
        rating = Rating.objects.get(type=rating_data["rating_type"])
        tournaments = (
            Tournament.public.filter(tournament_type__in=calculator.TOURNAMENT_TYPES)
            .filter(is_upcoming=False)
            .order_by("end_date")
        )

        print("Today =", today)
        print("Rating date =", rating_date)

        if specified_date:
            specified_date = datetime.datetime.strptime(specified_date, "%Y-%m-%d").date()
            RatingDate.objects.filter(rating=rating, date=specified_date).delete()

            dates_to_recalculate = [specified_date]
            self.calculate_rating(dates_to_recalculate, tournaments, calculator, rating)

            return

        with transaction.atomic():
            if from_zero:
                print("Erasing dates...")
                RatingDate.objects.filter(rating=rating).delete()
                RatingResult.objects.filter(rating=rating).delete()
                RatingDelta.objects.filter(rating=rating).delete()

            print("Calculating dates...")

            dates_to_process, rating_date = self.find_tournament_dates_changes(
                rating, rating_date, today, tournaments, calculator, tournaments_diff
            )

            important_dates = [
                # ERMC 2019 qualification date
                datetime.date(2019, 1, 1),
                # WRC 2020 qualification date
                datetime.date(2020, 2, 1),
                # Online tournaments qualification date
                datetime.date(2021, 2, 1),
            ]

            dates_to_process = dates_to_process + important_dates
            # make sure that all dates are unique
            dates_to_process = sorted(list(set(dates_to_process)))
            # it is important to skip the first date here
            # otherwise this date will be always added to the rating
            dates_to_process = dates_to_process[1:]

            print("Found dates: {}".format(len(dates_to_process)))

            already_added_dates = RatingDate.objects.filter(rating=rating).values_list("date", flat=True)
            dates_to_recalculate = sorted(list(set(dates_to_process) - set(already_added_dates)))

            print("Dates to recalculate: {}".format(len(dates_to_recalculate)))

            self.calculate_rating(dates_to_recalculate, tournaments, calculator, rating)

            # print('Calculating future dates...')
            #
            # future_dates = [
            # ]
            #
            # latest_future_date = future_dates[-1]
            #
            # dates_to_process, _ = self.find_tournament_dates_changes(
            #     rating,
            #     rating_date,
            #     latest_future_date,
            #     tournaments,
            #     calculator,
            #     tournaments_diff
            # )
            #
            # dates_to_recalculate = sorted(list(set(dates_to_process + future_dates)))
            # print('Dates to process: {}'.format(len(dates_to_recalculate)))
            #
            # first_future_date = dates_to_recalculate[0]
            # print('First future date =', first_future_date)
            # RatingDate.objects.filter(
            #     rating=rating, date__gte=first_future_date
            # ).delete()
            # RatingResult.objects.filter(
            #     rating=rating, date__gte=first_future_date
            # ).delete()
            # RatingDelta.objects.filter(
            #     rating=rating, date__gte=first_future_date
            # ).delete()
            #
            # self.calculate_rating(
            #     dates_to_recalculate,
            #     tournaments,
            #     calculator,
            #     rating,
            #     is_future=True
            # )

        print("{0}: End".format(get_date_string()))

    def calculate_rating(self, dates_to_process, tournaments, calculator, rating, is_future=False):
        for rating_date in dates_to_process:
            RatingDate.objects.create(rating=rating, date=rating_date, is_future=is_future)

            RatingResult.objects.filter(rating=rating, date=rating_date).delete()
            RatingDelta.objects.filter(rating=rating, date=rating_date).delete()

            limited_tournaments = tournaments.filter(end_date__lte=rating_date)
            print(rating_date, limited_tournaments.count())

            for tournament in limited_tournaments:
                calculator.calculate_players_deltas(tournament, rating, rating_date)

            calculator.calculate_players_rating_rank(rating, rating_date)

    def find_tournament_dates_changes(self, rating, start_date, stop_date, tournaments, calculator, tournaments_diff):
        continue_work = True
        dates_to_process = []
        while continue_work:
            need_to_recalculate = False

            # we need to rebuild rating only after changes in tournaments
            # there is no need to rebuild it each day
            limited_tournaments = tournaments.filter(end_date__lte=start_date)
            for tournament in limited_tournaments:
                # we don't want to add foreign ema tournaments without russian players
                # to the dates calculations
                if tournament.tournament_type == Tournament.FOREIGN_EMA and rating.type != Rating.EMA:
                    has_russian_players = (
                        TournamentResult.objects.filter(tournament=tournament)
                        .filter(player__country__code="RU")
                        .exists()
                    )
                    if not has_russian_players:
                        continue

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
