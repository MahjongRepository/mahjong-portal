from datetime import timedelta

from django.db.models import Sum

from player.models import Player
from rating.models import RatingDelta
from tournament.models import TournamentResult

INCLUDED_DAYS = 2 * 365
TOURNAMENT_RESULTS = 10


class InnerRatingCalculation(object):
    players = None

    def calculate_players_deltas(self, tournament, rating):
        """
        Load all tournament results and recalculate players rating position
        :param tournament: Tournament model
        :param rating: Rating model
        :return:
        """

        self.players = list(Player.all_objects.all())

        results = (TournamentResult.objects
                   .filter(tournament=tournament)
                   .prefetch_related('tournament'))

        for result in results:
            player = None

            for player_iter in self.players:
                if player_iter.id == result.player_id:
                    player = player_iter

            rating_delta = self.calculate_rating_delta(result)

            place_before = 0
            if RatingDelta.objects.filter(player=player, rating=rating).exists():
                place_before = player.inner_rating_place

            RatingDelta.objects.create(tournament=result.tournament,
                                       tournament_place=result.place,
                                       rating=rating,
                                       player=player,
                                       delta=rating_delta,
                                       rating_place_before=place_before)

            if not player.inner_rating_score:
                player.inner_rating_score = 0

            player.inner_rating_score += rating_delta

        self._recalculate_players_positions(tournament, rating)

        for player in self.players:
            player.save()

    def calculate_tournament_coefficient(self, tournament):
        """
        Increase or decrease tournament coefficient
        based on it's properties
        :param tournament: Tournament model
        :return:
        """
        base = 100
        calculated = base

        # Players

        if tournament.number_of_players <= 16:
            calculated -= 20

        if tournament.number_of_players >= 40:
            calculated += 10

        if tournament.number_of_players >= 60:
            calculated += 5

        if tournament.number_of_players >= 80:
            calculated += 5

        # Sessions

        if tournament.number_of_sessions <= 4:
            calculated -= 20

        if tournament.number_of_sessions >= 10:
            calculated += 10

        if tournament.number_of_sessions >= 12:
            calculated += 20

        return float(calculated / 100)

    def calculate_base_rank(self, tournament_result):
        """
        First place 1000 points
        In the middle of the table 0 points
        Last place -1000 points
        And other places between these marks
        from 1 to middle = positive score
        from middle to last = negative score
        :param tournament_result: array of TournamentResults models
        :return:
        """
        number_of_players = tournament_result.tournament.number_of_players
        place = tournament_result.place
        middle = number_of_players / 2

        # first place
        if place == 1:
            return 1000

        # last place
        if place == middle:
            return 0

        if place == number_of_players:
            return -1000

        calculated = round(((number_of_players - place - middle) / (number_of_players - middle - 1)) * 1000)

        return calculated

    def calculate_rating_delta(self, tournament_result):
        """
        Tournament coefficient * player base tournament rank
        :param tournament_result: array of TournamentResults models
        :return:
        """
        tournament_coefficient = self.calculate_tournament_coefficient(tournament_result.tournament)
        base_rank = self.calculate_base_rank(tournament_result)
        return round(tournament_coefficient * base_rank)

    def _recalculate_players_positions(self, tournament, rating):
        """
        To be able properly set positions deltas (eg. 12 place -> 1 place)
        we need to recalculate players positions after each tournament
        :param tournament: Tournament model
        :param rating: Rating model
        :return:
        """
        self._chose_active_tournament_results(tournament, rating)

        self.players = self._sort_players_by_scores(self.players)

        deltas = RatingDelta.objects.filter(tournament=tournament, rating=rating).prefetch_related('player')
        for delta in deltas:
            for player in self.players:
                if player.id == delta.player_id:
                    delta.rating_place_after = player.inner_rating_place
                    delta.save()

    def _chose_active_tournament_results(self, tournament, rating):
        """
        Method to decide what results we will use for rating.
        In this rating it will be last TOURNAMENT_RESULTS (int)
        from last INCLUDED_DAYS
        :param tournament: Tournament model
        :param rating: Rating model
        :return:
        """

        for player in self.players:
            two_years_ago = tournament.end_date - timedelta(days=INCLUDED_DAYS)
            last_results = (RatingDelta.objects
                                .filter(player=player)
                                .filter(rating=rating)
                                .filter(tournament__end_date__gte=two_years_ago)
                                .order_by('-tournament__end_date')[:TOURNAMENT_RESULTS])

            score = last_results.aggregate(Sum('delta'))['delta__sum']

            last_results_ids = [x.id for x in last_results]

            # we need it to display on user page active deltas
            RatingDelta.objects.filter(player=player, rating=rating).update(is_active=False)
            RatingDelta.objects.filter(id__in=last_results_ids, rating=rating).update(is_active=True)

            player.inner_rating_score = score

        self.players = self._sort_players_by_scores(self.players)
        place = 1

        for player in self.players:
            player.inner_rating_place = place

            place += 1

    def _sort_players_by_scores(self, players):
        return sorted(players, key=lambda x: (x.inner_rating_score is not None, x.inner_rating_score), reverse=True)
