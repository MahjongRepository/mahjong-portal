from datetime import timedelta

from django.db.models import Sum
from django.utils import timezone

from player.models import Player
from rating.models import RatingDelta, RatingResult
from settings.models import Country
from tournament.models import TournamentResult

INCLUDED_DAYS = 2 * 365
TOURNAMENT_RESULTS = 10


class InnerRatingCalculation(object):
    players = None

    def get_players(self):
        """
        Determine what players should be participated in the rating
        :return:
        """
        return list(Player.objects.filter(country__code='RU'))

    def calculate_players_deltas(self, tournament, rating):
        """
        Load all tournament results and recalculate players rating position
        :param tournament: Tournament model
        :param rating: Rating model
        :return:
        """

        self.players = self.get_players()

        results = (TournamentResult.objects
                   .filter(tournament=tournament)
                   .prefetch_related('tournament'))

        for player in self.players:
            player.rating_result, _ = RatingResult.objects.get_or_create(rating=rating, player=player)

        for result in results:
            # this method to find player is here for queries optimization
            player = None
            for player_iter in self.players:
                if player_iter.id == result.player_id:
                    player = player_iter

            # player not should be visible in our rating
            if not player:
                continue

            rating_delta = self.calculate_rating_delta(result)

            RatingDelta.objects.create(tournament=result.tournament,
                                       tournament_place=result.place,
                                       rating=rating,
                                       player=player,
                                       delta=rating_delta)

            if not player.rating_result.score:
                player.rating_result.score = 0

            player.rating_result.score += rating_delta

        self._chose_active_tournament_results(tournament, rating)

        for player in self.players:
            player.rating_result.save()

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

        if tournament.number_of_players <= 16 and tournament.number_of_players != 0:
            calculated -= 20

        if tournament.number_of_players >= 40:
            calculated += 10

        if tournament.number_of_players >= 60:
            calculated += 5

        if tournament.number_of_players >= 80:
            calculated += 5

        # Sessions

        if tournament.number_of_sessions <= 4 and tournament.number_of_sessions != 0:
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
            two_years_ago = timezone.now() - timedelta(days=INCLUDED_DAYS)
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

            player.rating_result.score = score

        self.players = self._sort_players_by_scores(self.players)

        place = 1
        for player in self.players:
            player.rating_result.place = place
            place += 1

    def _sort_players_by_scores(self, players):
        return sorted(players, key=lambda x: (x.rating_result.score is not None, x.rating_result.score), reverse=True)
