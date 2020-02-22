import csv
import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone

from player.models import Player
from rating.calculation.rr import RatingRRCalculation
from rating.models import Rating, RatingDelta, RatingResult, TournamentCoefficients
from tournament.models import Tournament, TournamentResult


def get_date_string():
    return timezone.now().strftime("%H:%M:%S")


class Command(BaseCommand):
    def handle(self, *args, **options):
        rating_date = datetime.date(2020, 2, 1)
        add_coefficient = True

        players = 40
        sessions = 10

        tournament = Tournament.objects.get(id=431)
        tournament.is_upcoming = False
        tournament.number_of_players = players
        tournament.number_of_sessions = sessions
        tournament.save()

        data = [["Игроков", players, "Игр", sessions, "Коэффициент"]]

        # Леонтьев 154
        # Алексеева 389
        # Монаков 70
        player_id = 70

        places = [1, 6, 10, 16, 20, 24, 30, 40]
        for place in places:
            print(place)
            data.append([""])
            data.append(["Место на турнире", "{}/{}".format(place, players)])
            data.append(["Рейтинг"])

            TournamentResult.objects.filter(tournament=tournament).delete()

            player = Player.objects.get(id=player_id)
            TournamentResult.objects.create(
                place=place, player=player, tournament=tournament
            )

            calculator = RatingRRCalculation()
            rating = Rating.objects.get(type=Rating.RR)
            types = [Tournament.RR, Tournament.EMA, Tournament.FOREIGN_EMA]
            tournaments = (
                Tournament.public.filter(tournament_type__in=types)
                .filter(is_upcoming=False)
                .order_by("end_date")
            )

            RatingResult.objects.filter(rating=rating).delete()
            RatingDelta.objects.filter(rating=rating).delete()

            dates_to_process = [rating_date]

            self.calculate_rating(dates_to_process, tournaments, calculator, rating)

            results = RatingResult.objects.filter(
                rating=rating, date=rating_date
            ).order_by("place")[:15]
            for result in results:
                data.append([result.player.last_name_ru, result.place, result.score])

            c = TournamentCoefficients.objects.get(
                rating=rating, date=rating_date, tournament=tournament
            )

            if add_coefficient:
                data[0].append(c.coefficient)
                add_coefficient = False

            with open("export.csv", "w") as f:
                writer = csv.writer(f)
                for x in data:
                    writer.writerow(x)

    def calculate_rating(self, dates_to_process, tournaments, calculator, rating):
        for i, rating_date in enumerate(dates_to_process):
            limited_tournaments = tournaments.filter(end_date__lte=rating_date)

            for tournament in limited_tournaments:
                calculator.calculate_players_deltas(tournament, rating, rating_date)

            calculator.calculate_players_rating_rank(rating, rating_date)
