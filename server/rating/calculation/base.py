
class BaseRating(object):
    players = None

    def __init__(self):
        self.players = self.get_players()

    def get_players(self):
        """
        Determine what players should be participated in the rating
        """
        raise NotImplemented

    def calculate_tournament_coefficient(self, tournament):
        """
        Increase or decrease tournament coefficient
        based on it's properties
        """
        raise NotImplemented

    def calculate_base_rank(self, tournament_result):
        """
        Base rank for the player based on his tournament place
        """
        raise NotImplemented

    def calculate_rating_delta(self, tournament_result):
        """
        How much points player will get from tournament
        """
        raise NotImplemented

    def calculate_players_deltas(self, tournament, rating):
        """
        Calculate scores for each player participated in tournament
        """
        raise NotImplemented

    def calculate_players_scores(self, tournament, rating):
        """
        Load all tournament results and recalculate player's rating positions
        """
        raise NotImplemented
