from django.utils import timezone

from player.models import Player
from rating.models import RatingDelta, Rating
from rating.utils import make_random_letters_and_digit_string
from settings.models import TournamentType, Country
from tournament.models import Tournament, TournamentResult


class RatingTestMixin(object):
    country = None
    player = None
    tournament_type = None

    def set_up_initial_objects(self):
        self.country = Country.objects.create(code='RU', name='Russia')
        self.player = self.create_player()
        self.tournament_type = TournamentType.objects.create(name='ema')

    def create_tournament(self, players=1, sessions=1, start_date=None, end_date=None):
        start_date = start_date or timezone.now().date()
        end_date = end_date or timezone.now().date()
        return Tournament.objects.create(
            name='test',
            slug=make_random_letters_and_digit_string(),
            start_date=start_date,
            end_date=end_date,
            country=self.country,
            tournament_type=self.tournament_type,
            number_of_players=players,
            number_of_sessions=sessions,
            tournament_coefficient=2,
            tournament_age=100
        )

    def create_player(self):
        return Player.objects.create(
            first_name='test',
            last_name='test',
            slug=make_random_letters_and_digit_string(),
            country=self.country
        )

    def create_tournament_result(self, tournament, place, player=None):
        player = player or self.player
        return TournamentResult.objects.create(
            place=place,
            tournament=tournament,
            player=player
        )

    def create_rating_delta(self, rating, tournament, player, delta):
        return RatingDelta.objects.create(
            tournament=tournament,
            tournament_place=1,
            rating=rating,
            player=player,
            delta=delta,
            base_rank=0,
        )
