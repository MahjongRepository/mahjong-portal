from django.test import TestCase

from online.handler import TournamentHandler
from online.models import TournamentStatus, TournamentPlayers, TournamentGame
from rating.mixins import RatingTestMixin
from rating.utils import make_random_letters_and_digit_string


class OnlineTournamentTestCase(TestCase, RatingTestMixin):

    def setUp(self):
        self.set_up_initial_objects()

    def test_start_new_round(self):
        tournament = self.create_tournament(sessions=2)
        handler = TournamentHandler(tournament=tournament)

        status = TournamentStatus.objects.get(tournament=tournament)
        self.assertEqual(status.current_round, None)

        handler.start_next_round()

        status = TournamentStatus.objects.get(tournament=tournament)
        self.assertEqual(status.current_round, 1)

        handler.start_next_round()

        status = TournamentStatus.objects.get(tournament=tournament)
        self.assertEqual(status.current_round, 2)

        handler.start_next_round()

        status = TournamentStatus.objects.get(tournament=tournament)
        self.assertEqual(status.current_round, 2)

    def test_start_new_round_and_prepare_games(self):
        tournament = self.create_tournament(sessions=3)
        handler = TournamentHandler(tournament=tournament)

        for x in range(0, 5):
            TournamentPlayers.objects.create(tournament=tournament,
                                             telegram_username=make_random_letters_and_digit_string(),
                                             tenhou_username=make_random_letters_and_digit_string(8))

        games, _ = handler.start_next_round()
        self.assertEqual(len(games), 2)

        for game in games:
            self.assertEqual(game.status, TournamentGame.NEW)
            self.assertEqual(game.game_players.all().distinct().count(), 4)
