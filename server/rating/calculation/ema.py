from player.models import Player
from rating.calculation.inner import InnerRatingCalculation
from settings.models import TournamentType
from tournament.models import Tournament, TournamentResult


class EmaRatingCalculation(InnerRatingCalculation):

    def get_players(self):
        """
        Determine what players should be participated in the rating
        :return:
        """
        results = TournamentResult.objects.exclude(tournament__tournament_type__slug=TournamentType.CLUB)
        return list(Player.objects.filter(id__in=results.values_list('player_id', flat=True)))
