from datetime import timedelta

from dateutil.relativedelta import relativedelta
from django.utils import timezone

from player.models import Player
from rating.calculation.base import BaseRating
from rating.models import RatingDelta, RatingResult
from tournament.models import TournamentResult


class InnerRatingCalculation(BaseRating):
    players = None

    def get_players(self):
        """
        Determine what players should be participated in the rating
        :return:
        """
        return list(Player.objects.filter(country__code='RU'))

    def calculate_players_rating_rank(self, rating):
        results = []
        two_years_ago = timezone.now().date() - timedelta(days=365 * 2)

        max_k = 5.3
        first_part_weight = 75
        second_part_weight = 25

        RatingResult.objects.filter(rating=rating).delete()

        for player in self.players:
            deltas = (RatingDelta.objects
                                 .filter(rating=rating, player=player)
                                 .filter(tournament__end_date__gte=two_years_ago))
            count_deltas = deltas.count()

            if count_deltas < 2:
                continue

            if deltas.count() <= count_deltas:
                tournaments_results = deltas
            else:
                limit = self._determine_tournaments_number(deltas.count())
                tournaments_results = deltas.order_by('-delta')[:limit]

            deltas.update(is_active=False)
            tournaments_results.update(is_active=True)

            first_part_numerator = 0
            first_part_denominator = 0

            for result in tournaments_results:
                first_part_numerator += float(result.delta)
                first_part_denominator += float(self._calculate_percentage(float(result.tournament_coefficient), result.tournament_age))

            first_part = first_part_numerator / first_part_denominator

            second_part_numerator = 0
            second_part_denominator = 4 * max_k

            best_results = deltas.order_by('-delta')[:4]
            for result in best_results:
                second_part_numerator += float(result.delta)

            second_part = second_part_numerator / second_part_denominator

            score = self._calculate_percentage(first_part, first_part_weight) + self._calculate_percentage(second_part, second_part_weight)

            results.append(RatingResult.objects.create(
                rating=rating,
                player=player,
                score=score,
                place=0
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

            delta, base_rank, players_coefficient, sessions_coefficient, tournament_age = self.calculate_rating_delta(result)

            RatingDelta.objects.create(tournament=result.tournament,
                                       tournament_place=result.place,
                                       rating=rating,
                                       player=player,
                                       delta=delta,
                                       players_coefficient=players_coefficient,
                                       sessions_coefficient=sessions_coefficient,
                                       tournament_coefficient=players_coefficient + sessions_coefficient,
                                       base_rank=base_rank,
                                       tournament_age=tournament_age)

    def calculate_tournament_coefficient(self, tournament):
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

        players_coefficient = self.players_coefficient(tournament)
        sessions_coefficient = self.sessions_coefficient(tournament)
        tournament_coefficient = players_coefficient + sessions_coefficient

        base_rank = self.calculate_base_rank(tournament_result)

        tournament_age = self._determine_tournament_age_weight(tournament)

        delta = tournament_coefficient * base_rank
        delta = self._calculate_percentage(delta, tournament_age)

        return delta, base_rank, players_coefficient, sessions_coefficient, tournament_age

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
        elif 81 <= tournament.number_of_players <= 120:
            second_part = players_multiplicator - 20

            calculated += 20 * 10 + second_part * second_value
        else:
            calculated += 250

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
                calculated += tournament.number_of_sessions * first_value
            elif 8 < tournament.number_of_sessions <= 12:
                calculated += 8 * first_value + (tournament.number_of_sessions - 8) * second_value
            elif 12 < tournament.number_of_sessions <= 16:
                calculated += 8 * first_value + 4 * second_value + (tournament.number_of_sessions - 12) * third_value
            elif 16 < tournament.number_of_sessions <= 20:
                calculated += 8 * first_value + 4 * second_value + 4 * third_value + (tournament.number_of_sessions - 16) * fourth_value

        return float(calculated / 100)

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
        return round(self._calculate_percentage(number_of_tournaments, 80)) + 1

    def _determine_tournament_age_weight(self, tournament):
        """
        Check about page for detailed description
        """

        today = timezone.now().date()
        end_date = tournament.end_date
        diff = relativedelta(today, end_date)
        months = diff.years * 12 + diff.months + diff.days / 30

        if months <= 12:
            return 100
        elif 13 <= months <= 18:
            return 66
        elif 19 <= months <= 24:
            return 33
        else:
            return 0

    def _calculate_percentage(self, number, percentage):
        if percentage == 100:
            return number

        if percentage == 0:
            return 0

        return (float(percentage) / 100.0) * number
