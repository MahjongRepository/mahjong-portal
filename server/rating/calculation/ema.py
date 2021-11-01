from datetime import timedelta

from dateutil.relativedelta import relativedelta
from django.template.defaultfilters import floatformat
from django.utils import timezone

from player.models import Player
from rating.calculation.rr import RatingRRCalculation
from rating.models import RatingDelta, RatingResult, TournamentCoefficients
from tournament.models import Tournament, TournamentResult
from utils.general import get_tournament_coefficient


class RatingEMACalculation(RatingRRCalculation):
    TOURNAMENT_TYPES = [Tournament.EMA, Tournament.FOREIGN_EMA, Tournament.CHAMPIONSHIP]
    IS_EMA = True

    def get_players(self):
        return list(
            Player.objects.exclude(ema_id="")
            .exclude(ema_id=None)
            .exclude(is_replacement=True)
            .exclude(is_hide=True)
            .order_by("-last_name")
        )

    def get_date(self, rating_date):
        # two years ago
        return rating_date - timedelta(days=365 * 2)

    def calculate_players_rating_rank(self, rating, rating_date):
        results = []
        two_years_ago = self.get_date(rating_date)

        # it is important to save rating updates time
        rating.updated_on = timezone.now()
        rating.save()

        base_query = self.get_base_query(rating, two_years_ago, rating_date)

        tournament_ids = base_query.values_list("tournament_id", flat=True).distinct()
        coefficient_temp = TournamentCoefficients.objects.filter(
            tournament_id__in=tournament_ids, rating=rating, date=rating_date
        )
        coefficients_cache = {}
        coefficients = []
        for coefficient in coefficient_temp:
            coefficients_cache[coefficient.tournament_id] = coefficient

        coefficients = sorted(coefficients, key=lambda x: x["value"], reverse=True)
        selected_coefficients = coefficients[: self.SECOND_PART_MIN_TOURNAMENTS]

        if len(selected_coefficients) < self.SECOND_PART_MIN_TOURNAMENTS:
            missed_tournaments = self.SECOND_PART_MIN_TOURNAMENTS - len(selected_coefficients)
            for _ in range(missed_tournaments):
                selected_coefficients.append({"coefficient": 1, "age": 100, "value": 1})

        max_coefficient = sum([x["value"] for x in selected_coefficients])

        for player in self.players:
            # we need to reduce SQL queries with this filter
            deltas = []
            for x in base_query:
                if x.player_id == player.id:
                    deltas.append(x)
            total_tournaments = len(deltas)

            if total_tournaments < self.MIN_TOURNAMENTS_NUMBER:
                continue

            if total_tournaments <= self.FIRST_PART_MIN_TOURNAMENTS:
                tournaments_results = deltas
            else:
                limit = self._determine_tournaments_number(total_tournaments)
                tournaments_results = sorted(deltas, key=lambda x: (x.base_rank, x.tournament.end_date), reverse=True)[
                    :limit
                ]

            best_rating_calculation, best_score = self._calculate_player_rating(
                player, tournaments_results, deltas, coefficients_cache, max_coefficient, selected_coefficients
            )
            best_tournament_results_option = tournaments_results

            RatingDelta.objects.filter(id__in=[x.id for x in best_tournament_results_option]).update(is_active=True)

            results.append(
                RatingResult(
                    rating=rating,
                    player=player,
                    score=best_score,
                    place=0,
                    rating_calculation=best_rating_calculation,
                    date=rating_date,
                    tournament_numbers=len(deltas),
                )
            )

        place = 1
        results = sorted(results, key=lambda x: x.score, reverse=True)
        for result in results:
            result.place = place
            place += 1

        RatingResult.objects.bulk_create(results)

    def _calculate_player_rating(
        self, player, tournaments_results, deltas, coefficients_cache, max_coefficient, selected_coefficients
    ):
        first_part_numerator_calculation = []
        first_part_denominator_calculation = []

        second_part_numerator_calculation = []
        second_part_denominator_calculation = []

        first_part_numerator = 0
        first_part_denominator = 0

        for result in tournaments_results:
            coefficient_obj = coefficients_cache[result.tournament_id]
            coefficient = get_tournament_coefficient(
                self.IS_EMA, coefficient_obj.tournament_id, player, coefficient_obj.coefficient
            )

            first_part_numerator += float(result.delta)
            first_part_denominator += float(self._calculate_percentage(float(coefficient), coefficient_obj.age))

            first_part_numerator_calculation.append(
                "{} * {} * {}".format(
                    floatformat(result.base_rank, -2),
                    floatformat(coefficient, -2),
                    floatformat(coefficient_obj.age / 100, -2),
                )
            )

            first_part_denominator_calculation.append(
                "{} * {}".format(floatformat(coefficient, -2), floatformat(coefficient_obj.age / 100, -2))
            )

        if len(tournaments_results) < self.FIRST_PART_MIN_TOURNAMENTS:
            fill_missed_data = self.FIRST_PART_MIN_TOURNAMENTS - len(tournaments_results)
            first_part_denominator += fill_missed_data

            for _ in range(0, fill_missed_data):
                first_part_numerator_calculation.append("0")
                first_part_denominator_calculation.append("1")

        first_part = first_part_numerator / first_part_denominator

        second_part_numerator = 0
        second_part_denominator = 0

        best_results = sorted(deltas, key=lambda x: (x.base_rank, x.tournament.end_date), reverse=True)[
            : self.SECOND_PART_MIN_TOURNAMENTS
        ]
        for result in best_results:
            coefficient_obj = coefficients_cache[result.tournament_id]
            coefficient = get_tournament_coefficient(
                self.IS_EMA, coefficient_obj.tournament_id, player, coefficient_obj.coefficient
            )

            second_part_numerator += float(result.delta)
            second_part_denominator += float(self._calculate_percentage(float(coefficient), coefficient_obj.age))

            second_part_numerator_calculation.append(
                "{} * {} * {}".format(
                    floatformat(result.base_rank, -2),
                    floatformat(coefficient, -2),
                    floatformat(coefficient_obj.age / 100, -2),
                )
            )

            second_part_denominator_calculation.append(
                "{} * {}".format(floatformat(coefficient, -2), floatformat(coefficient_obj.age / 100, -2))
            )

        if len(tournaments_results) < self.SECOND_PART_MIN_TOURNAMENTS:
            fill_missed_data = self.SECOND_PART_MIN_TOURNAMENTS - len(best_results)
            second_part_denominator += fill_missed_data

            for _ in range(0, fill_missed_data):
                second_part_numerator_calculation.append("0")
                second_part_denominator_calculation.append("1")

        second_part = second_part_numerator / second_part_denominator

        score = self._calculate_percentage(first_part, self.FIRST_PART_WEIGHT) + self._calculate_percentage(
            second_part, self.SECOND_PART_WEIGHT
        )

        first_part_calculation = "p1 = ({}) / ({}) = {}".format(
            " + ".join(first_part_numerator_calculation), " + ".join(first_part_denominator_calculation), first_part
        )
        second_part_calculation = "p2 = ({}) / ({}) = {}".format(
            " + ".join(second_part_numerator_calculation), " + ".join(second_part_denominator_calculation), second_part
        )
        total_calculation = "score = {} * {} + {} * {} = {}".format(
            first_part, self.FIRST_PART_WEIGHT / 100, second_part, self.SECOND_PART_WEIGHT / 100, score
        )
        rating_calculation = "\n\n".join((first_part_calculation, second_part_calculation, total_calculation))

        return rating_calculation, score

    def tournament_coefficient(self, tournament):
        return sum(
            [
                self.players_coefficient(tournament),
                self.duration_coefficient(tournament),
                self.countries_coefficient(tournament),
                self.qualification_coefficient(tournament),
            ]
        )

    def players_coefficient(self, tournament):
        if tournament.number_of_players <= 40:
            return 0.0
        elif 41 <= tournament.number_of_players <= 80:
            return 0.5
        else:
            return 1.0

    def duration_coefficient(self, tournament):
        diff = relativedelta(tournament.end_date, tournament.start_date)
        days = diff.days + 1
        if days > 3:
            days = 3
        return days

    def countries_coefficient(self, tournament):
        results = (
            TournamentResult.objects.filter(tournament=tournament)
            .filter(player__country__isnull=False)
            .values_list("player__country__code", flat=True)
            .distinct()
        )
        number_of_countries = len(results)
        if number_of_countries <= 5:
            return 0.0
        elif 5 < number_of_countries < 10:
            return 0.5
        else:
            return 1.0

    def qualification_coefficient(self, tournament):
        return tournament.tournament_type == Tournament.CHAMPIONSHIP and 1 or 0

    def tournament_age(self, end_date, rating_date):
        diff = relativedelta(rating_date, end_date)
        months = diff.years * 12 + diff.months + diff.days / 30

        if months <= 12:
            return 100
        elif 12 < months <= 24:
            return 50
        else:
            return 0
