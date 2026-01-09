# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand

from online.models import TournamentPlayers
from tournament.models import MsOnlineTournamentRegistration, OnlineTournamentRegistration, Tournament


class Command(BaseCommand):
    def get_team_key(self, object, from_tournament_players):
        if from_tournament_players:
            return object.team_name
        else:
            return object.notes

    def add_arguments(self, parser):
        parser.add_argument("tournament_id", type=int)
        parser.add_argument("is_pair", type=bool)
        parser.add_argument("from_tournament_players", type=bool)

    def handle(self, *args, **options):
        tournament_id = options["tournament_id"]
        is_pair = options["is_pair"]
        from_tournament_players = options["from_tournament_players"]
        tournament = Tournament.objects.get(id=tournament_id)

        assert tournament.tournament_type == Tournament.ONLINE

        if not tournament.is_majsoul_tournament:
            if not from_tournament_players:
                confirm_players = OnlineTournamentRegistration.objects.filter(
                    tournament_id=tournament_id,
                    is_approved=True,
                )
            else:
                confirm_players = TournamentPlayers.objects.filter(
                    tournament_id=tournament_id,
                    pantheon_id__isnull=False,
                    is_disable=False,
                )
        else:
            if not from_tournament_players:
                confirm_players = MsOnlineTournamentRegistration.objects.filter(
                    tournament_id=tournament_id,
                    is_approved=True,
                )
            else:
                confirm_players = TournamentPlayers.objects.filter(
                    tournament_id=tournament_id,
                    pantheon_id__isnull=False,
                    is_disable=False,
                )

        print("Number of confirmed players: {}".format(confirm_players.count()))
        if is_pair:
            assert confirm_players.count() % 2 == 0
        else:
            assert confirm_players.count() % 4 == 0

        teams = {}
        for x in confirm_players:
            key = self.get_team_key(x, from_tournament_players)
            if key not in teams:
                teams[key] = []

            teams[key].append(x)

        for key in teams.keys():
            if is_pair:
                assert len(teams[key]) == 2, f"[{key}] = {len(teams[key])}"
                target_count = 2
            else:
                assert len(teams[key]) == 4, f"[{key}] = {len(teams[key])}"
                target_count = 4
            print(f"team=[{key}]: {target_count} players")

        print("All teams correct")
