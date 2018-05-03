from django.utils import timezone

from player.models import Player
from rating.models import RatingDelta
from utils.general import make_random_letters_and_digit_string
from settings.models import Country
from tournament.models import Tournament, TournamentResult


class RatingTestMixin(object):
    country = None
    player = None

    def set_up_initial_objects(self):
        self.country = Country.objects.create(code='RU', name='Russia')
        self.player = self.create_player()

    def create_tournament(self, players=1, sessions=1, start_date=None, end_date=None, need_qualification=False):
        start_date = start_date or timezone.now().date()
        end_date = end_date or timezone.now().date()
        return Tournament.objects.create(
            name='test',
            slug=make_random_letters_and_digit_string(),
            start_date=start_date,
            end_date=end_date,
            country=self.country,
            tournament_type=Tournament.EMA,
            number_of_players=players,
            number_of_sessions=sessions,
            need_qualification=need_qualification
        )

    def create_player(self, country_code=None):
        if country_code:
            country, _ = Country.objects.get_or_create(code=country_code, name=country_code)
        else:
            country = self.country

        return Player.objects.create(
            first_name='test',
            last_name='test',
            slug=make_random_letters_and_digit_string(),
            country=country
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
