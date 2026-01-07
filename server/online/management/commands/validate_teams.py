# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand

from tournament.models import MsOnlineTournamentRegistration, OnlineTournamentRegistration, Tournament


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("tournament_id", type=int)
        parser.add_argument("is_pair", type=bool)

    def handle(self, *args, **options):
        tournament_id = options["tournament_id"]
        is_pair = options["is_pair"]
        tournament = Tournament.objects.get(id=tournament_id)

        assert tournament.tournament_type == Tournament.ONLINE

        if not tournament.is_majsoul_tournament:
            confirm_players = OnlineTournamentRegistration.objects.filter(
                tournament_id=tournament_id,
                is_approved=True,
            )
        else:
            confirm_players = MsOnlineTournamentRegistration.objects.filter(
                tournament_id=tournament_id,
                is_approved=True,
            )

        print("Number of confirmed players: {}".format(confirm_players.count()))
        if is_pair:
            assert confirm_players.count() % 2 == 0
        else:
            assert confirm_players.count() % 4 == 0

        teams = {}
        for x in confirm_players:
            if x.notes not in teams:
                teams[x.notes] = []

            teams[x.notes].append(x)

        for key in teams.keys():
            if is_pair:
                assert len(teams[key]) == 2, f"[{key}] = {len(teams[key])}"
                target_count = 2
            else:
                assert len(teams[key]) == 4, f"[{key}] = {len(teams[key])}"
                target_count = 4
            print(f"team=[{key}]: {target_count} players")

        print("All teams correct")
