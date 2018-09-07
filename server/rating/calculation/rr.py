import math
from datetime import timedelta

from dateutil.relativedelta import relativedelta
from django.db.models import Q
from django.template.defaultfilters import floatformat
from django.utils import timezone

from player.models import Player
from rating.calculation.hardcoded_coefficients import AGARI_TOURNAMENT_ID, AGARI_FIRST_STAGE_COEFFICIENT, \
    AGARI_SECOND_STAGE_COEFFICIENT
from rating.models import RatingDelta, RatingResult, TournamentCoefficients
from tournament.models import TournamentResult, Tournament
from utils.general import get_tournament_coefficient


class RatingRRCalculation(object):
    players = None

    FIRST_PART_MIN_TOURNAMENTS = 5
    SECOND_PART_MIN_TOURNAMENTS = 4
    FIRST_PART_WEIGHT = 50
    SECOND_PART_WEIGHT = 50

    MIN_TOURNAMENTS_NUMBER = 2

    IS_EMA = False

    def __init__(self):
        self.players = self.get_players()

    def get_players(self):
        """
        Determine what players should be participated in the rating
        :return:
        """
        return list(Player.objects.filter(country__code='RU'))

    def get_base_query(self, rating, start_date, rating_date):
        base_query = (RatingDelta.objects
                      .filter(rating=rating)
                      .filter(Q(tournament__tournament_type=Tournament.RR) |
                              Q(tournament__tournament_type=Tournament.EMA) |
                              Q(tournament__tournament_type=Tournament.FOREIGN_EMA))
                      .filter(Q(tournament__end_date__gt=start_date) & Q(tournament__end_date__lte=rating_date))
                      .filter(date=rating_date))
        return base_query

    def get_date(self, rating_date):
        # two years ago
        return rating_date - timedelta(days=365 * 2)

    def calculate_players_rating_rank(self, rating, rating_date, is_last):
        results = []
        two_years_ago = self.get_date(rating_date)

        # it is important to save rating updates time
        rating.updated_on = timezone.now()
        rating.save()

        base_query = self.get_base_query(rating, two_years_ago, rating_date)

        tournament_ids = base_query.values_list('tournament_id', flat=True).distinct()
        coefficient_temp = TournamentCoefficients.objects.filter(
            tournament_id__in=tournament_ids,
            rating=rating,
            date=rating_date
        )
        coefficients_cache = {}
        coefficients = []
        for coefficient in coefficient_temp:
            coefficients_cache[coefficient.tournament_id] = coefficient

            c = self._calculate_percentage(float(coefficient.coefficient), coefficient.age)
            coefficients.append(c)

        # TODO: Remove these hardcoded values when tournaments with stages will be implemented
        if not rating.is_online() and AGARI_TOURNAMENT_ID in tournament_ids:
            tournament = Tournament.objects.get(id=AGARI_TOURNAMENT_ID)
            if tournament.end_date >= rating_date:
                age = self.tournament_age(tournament.end_date, rating_date)
                coefficients.append(self._calculate_percentage(AGARI_SECOND_STAGE_COEFFICIENT, age))
                coefficients.append(self._calculate_percentage(AGARI_FIRST_STAGE_COEFFICIENT, age))

        coefficients = sorted(coefficients, reverse=True)
        max_coefficient = sum(coefficients[:self.SECOND_PART_MIN_TOURNAMENTS])

        if len(coefficients) < self.SECOND_PART_MIN_TOURNAMENTS:
            max_coefficient += self.SECOND_PART_MIN_TOURNAMENTS - len(coefficients)

        for player in self.players:
            first_part_numerator_calculation = []
            first_part_denominator_calculation = []

            second_part_numerator_calculation = []

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
                tournaments_results = sorted(deltas, key=lambda x: x.base_rank, reverse=True)[:limit]

            if is_last:
                RatingDelta.objects.filter(id__in=[x.id for x in tournaments_results]).update(is_active=True)

            first_part_numerator = 0
            first_part_denominator = 0

            for result in tournaments_results:
                coefficient_obj = coefficients_cache[result.tournament_id]
                coefficient = get_tournament_coefficient(coefficient_obj.tournament_id, player, coefficient_obj.coefficient)

                first_part_numerator += float(result.delta)
                first_part_denominator += float(self._calculate_percentage(float(coefficient), coefficient_obj.age))

                if is_last:
                    first_part_numerator_calculation.append('{} * {} * {}'.format(
                        floatformat(result.base_rank, -2),
                        floatformat(coefficient, -2),
                        floatformat(coefficient_obj.age / 100, -2)
                    ))

                    first_part_denominator_calculation.append('{} * {}'.format(
                        floatformat(coefficient, -2),
                        floatformat(coefficient_obj.age / 100, -2)
                    ))

            if len(tournaments_results) < self.FIRST_PART_MIN_TOURNAMENTS:
                fill_missed_data = self.FIRST_PART_MIN_TOURNAMENTS - len(tournaments_results)
                first_part_denominator += fill_missed_data

                if is_last:
                    for x in range(0, fill_missed_data):
                        first_part_numerator_calculation.append('0')
                        first_part_denominator_calculation.append('1')

            first_part = first_part_numerator / first_part_denominator

            second_part_numerator = 0
            second_part_denominator = max_coefficient

            best_results = sorted(deltas, key=lambda x: x.delta, reverse=True)[:self.SECOND_PART_MIN_TOURNAMENTS]
            for result in best_results:
                coefficient_obj = coefficients_cache[result.tournament_id]
                coefficient = get_tournament_coefficient(coefficient_obj.tournament_id, player, coefficient_obj.coefficient)

                second_part_numerator += float(result.delta)

                if is_last:
                    second_part_numerator_calculation.append('{} * {} * {}'.format(
                        floatformat(result.base_rank, -2),
                        floatformat(coefficient, -2),
                        floatformat(coefficient_obj.age / 100, -2)
                    ))

            second_part = second_part_numerator / second_part_denominator

            score = self._calculate_percentage(first_part, self.FIRST_PART_WEIGHT) + self._calculate_percentage(second_part, self.SECOND_PART_WEIGHT)

            rating_calculation = ''
            if is_last:
                first_part_calculation = '({}) / ({})'.format(
                    ' + '.join(first_part_numerator_calculation), ' + '.join(first_part_denominator_calculation)
                )
                second_part_calculation = '({}) / {}'.format(
                    ' + '.join(second_part_numerator_calculation), max_coefficient
                )
                rating_calculation = '({}) * {} + ({}) * {}'.format(
                    first_part_calculation,
                    self.FIRST_PART_WEIGHT / 100,
                    second_part_calculation,
                    self.SECOND_PART_WEIGHT / 100
                )

            results.append(RatingResult(
                rating=rating,
                player=player,
                score=score,
                place=0,
                rating_calculation=rating_calculation,
                date=rating_date,
                is_last=is_last
            ))

        place = 1
        results = sorted(results, key=lambda x: x.score, reverse=True)
        for result in results:
            result.place = place
            place += 1

        RatingResult.objects.bulk_create(results)

    def calculate_players_deltas(self, tournament, rating, rating_date, is_last):
        """
        Load all tournament results and recalculate players rating position
        :param tournament: Tournament model
        :param rating: Rating model
        :param rating_date: Rating date
        :return:
        """

        coefficient_obj, _ = TournamentCoefficients.objects.get_or_create(
            rating=rating,
            tournament=tournament,
            date=rating_date
        )
        coefficient_obj.coefficient = self.tournament_coefficient(tournament)
        coefficient_obj.age = self.tournament_age(tournament.end_date, rating_date)
        if rating_date <= tournament.end_date:
            coefficient_obj.previous_age = 0
        else:
            coefficient_obj.previous_age = self.tournament_age(tournament.end_date, rating_date - timedelta(days=1))
        coefficient_obj.save()

        results = (TournamentResult.objects
                                   .filter(tournament=tournament)
                                   .filter(exclude_from_rating=False))

        deltas = []
        for result in results:
            # this method to find player is here for queries optimization
            player = None
            for player_iter in self.players:
                if player_iter.id == result.player_id:
                    player = player_iter

            # player not should be visible in our rating
            if not player:
                continue

            delta, base_rank = self.calculate_rating_delta(result, rating_date, tournament, player)

            deltas.append(RatingDelta(
                tournament=tournament,
                tournament_place=result.place,
                rating=rating,
                player=player,
                delta=delta,
                base_rank=base_rank,
                date=rating_date,
                is_last=is_last
            ))

        RatingDelta.objects.bulk_create(deltas)

    def tournament_coefficient(self, tournament):
        """
        Increase tournament coefficient based on it's properties
        """
        return self.players_coefficient(tournament) + self.sessions_coefficient(tournament)

    def calculate_base_rank(self, tournament_result, tournament):
        """
        First place 1000 points
        Last place 0 points
        And other places between these marks
        """
        number_of_players = tournament.number_of_players
        place = tournament_result.place

        # first place
        if place == 1:
            return 1000

        if place == number_of_players:
            return 0

        return ((number_of_players - place) / (number_of_players - 1)) * 1000

    def calculate_rating_delta(self, tournament_result, rating_date, tournament, player):
        """
        Determine player delta and tournament properties
        """
        tournament_coefficient = self.tournament_coefficient(tournament)
        tournament_coefficient = get_tournament_coefficient(tournament.id, player, tournament_coefficient)

        base_rank = self.calculate_base_rank(tournament_result, tournament)
        # for ema we had to round base rank
        if self.IS_EMA:
            base_rank = round(base_rank)

        tournament_age = self.tournament_age(tournament.end_date, rating_date)

        delta = tournament_coefficient * base_rank
        delta = self._calculate_percentage(delta, tournament_age)

        return delta, base_rank

    def players_coefficient(self, tournament):
        """
        Check about page for detailed description
        """
        calculated = 0
        players_multiplicator = tournament.number_of_players // 4

        first_value = 10
        second_value = 5

        if tournament.number_of_players <= 80:
            calculated += players_multiplicator * first_value
        elif 81 <= tournament.number_of_players <= 160:
            second_part = players_multiplicator - 20

            calculated += 20 * first_value + second_part * second_value
        else:
            calculated += 300

        return float(calculated / 100)

    def sessions_coefficient(self, tournament):
        """
        Check about page for detailed description
        """
        calculated = 0

        sessions = tournament.number_of_sessions

        # for EMA tournaments we don't know number of sessions :(
        if sessions == 0:
            sessions = self._assume_number_of_sessions(tournament)

        if sessions > 20:
            calculated += 280
        else:
            first_value = 20
            second_value = 15
            third_value = 10
            fourth_value = 5

            # need to find a better way to do it
            if sessions <= 8:
                calculated += sessions * first_value
            elif 8 < sessions <= 12:
                calculated += 8 * first_value + (sessions - 8) * second_value
            elif 12 < sessions <= 16:
                calculated += 8 * first_value + 4 * second_value + (sessions - 12) * third_value
            elif 16 < sessions <= 20:
                calculated += 8 * first_value + 4 * second_value + 4 * third_value + (sessions - 16) * fourth_value

        return float(calculated / 100)

    def tournament_age(self, end_date, rating_date):
        """
        Check about page for detailed description
        """

        diff = relativedelta(rating_date, end_date)

        if diff.years < 1:
            return 100
        elif diff.years < 2 and diff.months < 6:
            return 66
        elif diff.years < 2:
            return 33
        else:
            return 0

    def _assume_number_of_sessions(self, tournament):
        """
        If we don't know number of sessions for tournament
        we can assume them from number of days
        1 day = 4
        2 days = 8
        3+ days = 12
        """
        if not tournament.start_date or not tournament.end_date:
            return 0

        delta = tournament.end_date - tournament.start_date
        days = delta.days

        if days > 3:
            days = 3

        return days * 4

    def _determine_tournaments_number(self, number_of_tournaments):
        """
        5 tournaments is a base
        for additional calculations we are taking 80% of additional tournaments
        Check about page for detailed description
        """
        if number_of_tournaments <= 5:
            return number_of_tournaments

        n = number_of_tournaments - 5

        return 5 + math.ceil(self._calculate_percentage(n, 80))

    def _calculate_percentage(self, number, percentage):
        if percentage == 100:
            return number

        if percentage == 0:
            return 0

        return (float(percentage) / 100.0) * number
