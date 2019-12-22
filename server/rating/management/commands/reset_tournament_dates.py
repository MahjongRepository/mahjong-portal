import datetime

from django.core.management.base import BaseCommand

from rating.calculation.rr import RatingRRCalculation
from rating.models import RatingDate
from tournament.models import Tournament


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('tournament_id', type=int)

    def handle(self, *args, **options):
        tournament_id = options['tournament_id']
        tournament = Tournament.objects.get(id=tournament_id)

        today = datetime.datetime.now().date()
        tournament_date = tournament.end_date
        calculator = RatingRRCalculation()

        tournaments_diff = {}
        dates_to_process = []
        continue_work = True
        while continue_work:
            need_to_recalculate = False
            if tournament.id not in tournaments_diff:
                age = calculator.tournament_age(tournament.end_date, tournament_date)
                need_to_recalculate = True
                tournaments_diff[tournament.id] = age
            else:
                age = calculator.tournament_age(tournament.end_date, tournament_date)
                if tournaments_diff[tournament.id] != age:
                    need_to_recalculate = True
                    tournaments_diff[tournament.id] = age

            if need_to_recalculate:
                dates_to_process.append(tournament_date)

            tournament_date = tournament_date + datetime.timedelta(days=1)

            if tournament_date > today:
                continue_work = False

        print(dates_to_process)
        RatingDate.objects.filter(date__in=dates_to_process).delete()
