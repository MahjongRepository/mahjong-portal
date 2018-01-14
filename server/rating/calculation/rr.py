import math
from datetime import timedelta

from dateutil.relativedelta import relativedelta
from django.utils import timezone

from player.models import Player
from rating.models import RatingDelta, RatingResult, TournamentCoefficients
from tournament.models import TournamentResult, Tournament


class RatingRRCalculation(object):
    players = None

    FIRST_PART_MIN_TOURNAMENTS = 5
    SECOND_PART_MIN_TOURNAMENTS = 4
    FIRST_PART_WEIGHT = 50
    SECOND_PART_WEIGHT = 50
    MIN_PLAYERS_REQUIREMENTS = 16
    NEED_QUALIFICATION = False
    HAS_ACCREDITATION = True

    def __init__(self):
        self.players = self.get_players()

    def get_players(self):
        """
        Determine what players should be participated in the rating
        :return:
        """
        return list(Player.objects.filter(country__code='RU'))

    def calculate_players_rating_rank(self, rating):
        results = []
        two_years_ago = timezone.now().date() - timedelta(days=365 * 2)

        # it is important to save rating updates time
        rating.updated_on = timezone.now()
        rating.save()

        base_query = (RatingDelta.objects
                                 .filter(rating=rating)
                                 .filter(tournament__number_of_players__gte=self.MIN_PLAYERS_REQUIREMENTS)
                                 .filter(tournament__need_qualification=self.NEED_QUALIFICATION)
                                 .filter(tournament__end_date__gte=two_years_ago))

        if self.HAS_ACCREDITATION:
            base_query = base_query.filter(tournament__has_accreditation=self.HAS_ACCREDITATION)

        tournament_ids = base_query.values_list('tournament_id', flat=True).distinct()
        coefficient_temp = Tournament.objects.filter(id__in=tournament_ids)

        coefficients_cache = {}

        coefficients = []
        for item in coefficient_temp:
            coefficient = TournamentCoefficients.objects.get(rating=rating, tournament=item)
            coefficients_cache[item.id] = coefficient

            c = self._calculate_percentage(float(coefficient.coefficient), coefficient.age)
            coefficients.append(c)

        coefficients = sorted(coefficients, reverse=True)
        max_coefficient = sum(coefficients[:self.SECOND_PART_MIN_TOURNAMENTS])

        if len(coefficients) < self.SECOND_PART_MIN_TOURNAMENTS:
            max_coefficient += self.SECOND_PART_MIN_TOURNAMENTS - len(coefficients)

        RatingResult.objects.filter(rating=rating).delete()

        for player in self.players:

            first_part_numerator_calculation = []
            first_part_denominator_calculation = []

            second_part_numerator_calculation = []

            deltas = base_query.filter(player=player)
            total_tournaments = deltas.count()

            if total_tournaments < 2:
                continue

            if total_tournaments <= self.FIRST_PART_MIN_TOURNAMENTS:
                tournaments_results = deltas
            else:
                limit = self._determine_tournaments_number(deltas.count())
                tournaments_results = deltas.order_by('-base_rank')[:limit]

            RatingDelta.objects.filter(id__in=[x.id for x in deltas]).update(is_active=False)
            RatingDelta.objects.filter(id__in=[x.id for x in tournaments_results]).update(is_active=True)

            first_part_numerator = 0
            first_part_denominator = 0

            for result in tournaments_results:
                coefficient = coefficients_cache[result.tournament_id]

                first_part_numerator += float(result.delta)
                first_part_denominator += float(self._calculate_percentage(float(coefficient.coefficient), coefficient.age))

                first_part_numerator_calculation.append('{} * {} * {}'.format(result.base_rank, coefficient.coefficient, coefficient.age / 100))
                first_part_denominator_calculation.append('{} * {}'.format(coefficient.coefficient, coefficient.age / 100))

            if len(tournaments_results) < self.FIRST_PART_MIN_TOURNAMENTS:
                fill_missed_data = self.FIRST_PART_MIN_TOURNAMENTS - len(tournaments_results)
                first_part_denominator += fill_missed_data

                for x in range(0, fill_missed_data):
                    first_part_numerator_calculation.append('0')
                    first_part_denominator_calculation.append('1')

            first_part = first_part_numerator / first_part_denominator

            second_part_numerator = 0
            second_part_denominator = max_coefficient

            best_results = deltas.order_by('-delta')[:self.SECOND_PART_MIN_TOURNAMENTS]
            for result in best_results:
                coefficient = coefficients_cache[result.tournament_id]

                second_part_numerator += float(result.delta)

                second_part_numerator_calculation.append('{} * {} * {}'.format(result.base_rank, coefficient.coefficient, coefficient.age / 100))

            second_part = second_part_numerator / second_part_denominator

            score = self._calculate_percentage(first_part, self.FIRST_PART_WEIGHT) + self._calculate_percentage(second_part, self.SECOND_PART_WEIGHT)

            first_part_calculation = '({}) / ({})'.format(' + '.join(first_part_numerator_calculation), ' + '.join(first_part_denominator_calculation))
            second_part_calculation = '({}) / {}'.format(' + '.join(second_part_numerator_calculation), max_coefficient)
            rating_calculation = '({}) * {} + ({}) * {}'.format(first_part_calculation, self.FIRST_PART_WEIGHT / 100, second_part_calculation, self.SECOND_PART_WEIGHT / 100)

            results.append(RatingResult.objects.create(
                rating=rating,
                player=player,
                score=score,
                place=0,
                rating_calculation=rating_calculation
            ))

        place = 1
        results = sorted(results, key=lambda x: x.score, reverse=True)
        for result in results:
            result.place = place
            result.save()

            place += 1

    def calculate_players_deltas(self, tournament, rating):
        """
        Load all tournament results and recalculate players rating position
        :param tournament: Tournament model
        :param rating: Rating model
        :return:
        """

        coefficient_obj, _ = TournamentCoefficients.objects.get_or_create(rating=rating, tournament=tournament)
        coefficient_obj.coefficient = self.tournament_coefficient(tournament)
        coefficient_obj.age = self.tournament_age(tournament)
        coefficient_obj.save()

        results = (TournamentResult.objects
                                   .filter(tournament=tournament)
                                   .prefetch_related('tournament'))

        for result in results:
            # this method to find player is here for queries optimization
            player = None
            for player_iter in self.players:
                if player_iter.id == result.player_id:
                    player = player_iter

            # player not should be visible in our rating
            if not player:
                continue

            delta, base_rank = self.calculate_rating_delta(result)

            RatingDelta.objects.create(tournament=result.tournament,
                                       tournament_place=result.place,
                                       rating=rating,
                                       player=player,
                                       delta=delta,
                                       base_rank=base_rank)

    def tournament_coefficient(self, tournament):
        """
        Increase tournament coefficient based on it's properties
        """
        return self.players_coefficient(tournament) + self.sessions_coefficient(tournament)

    def calculate_base_rank(self, tournament_result):
        """
        First place 1000 points
        Last place 0 points
        And other places between these marks
        """
        number_of_players = tournament_result.tournament.number_of_players
        place = tournament_result.place

        # first place
        if place == 1:
            return 1000

        if place == number_of_players:
            return 0

        return ((number_of_players - place) / (number_of_players - 1)) * 1000

    def calculate_rating_delta(self, tournament_result):
        """
        Determine player delta and tournament properties
        """
        tournament = tournament_result.tournament
        tournament_coefficient = self.tournament_coefficient(tournament)

        base_rank = self.calculate_base_rank(tournament_result)

        tournament_age = self.tournament_age(tournament)

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

    def tournament_age(self, tournament):
        """
        Check about page for detailed description
        """

        today = timezone.now().date()
        end_date = tournament.end_date
        diff = relativedelta(today, end_date)
        months = diff.years * 12 + diff.months + diff.days / 30

        if months <= 12:
            return 100
        elif 12 < months <= 18:
            return 66
        elif 18 < months <= 24:
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
