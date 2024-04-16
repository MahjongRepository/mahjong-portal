# -*- coding: utf-8 -*-

import os
import random

import ujson as json
from django.conf import settings

from online.models import TournamentPlayers


class TeamSeating:
    initial_seating = os.path.join(settings.BASE_DIR, "shared", "initial_seating.txt")
    processed_seating = os.path.join(settings.BASE_DIR, "shared", "team_seating.json")

    @staticmethod
    def get_seating_for_round(round_number):
        # handler will send us 1..7 numbers
        round_index = round_number - 1
        assert round_index >= 0

        with open(TeamSeating.processed_seating) as f:
            data = json.loads(f.read())

        seating = data["seating"][round_index]

        for table in seating:
            # replace team numbers with pantheon ids
            for x in range(0, 4):
                table[x] = data["team_players_map"][str(table[x])]

        return seating

    @staticmethod
    def prepare_team_sortition():
        confirm_players = TournamentPlayers.objects.filter(
            tournament_id=settings.TOURNAMENT_ID, pantheon_id__isnull=False
        )
        confirm_players.update(team_number=None)

        print("Number of confirmed players: {}".format(confirm_players.count()))
        assert confirm_players.count() % 4 == 0

        teams = {}
        for x in confirm_players:
            if x.team_name not in teams:
                teams[x.team_name] = []

            teams[x.team_name].append(x)

        # we need to be sure that there is only 4 players in all teams
        for key in teams.keys():
            assert len(teams[key]) == 4, f"{key} = {len(teams[key])}"

        team_players_map = {}

        # let's set team numbers
        for i, key in enumerate(sorted(teams.keys())):
            initial = i * 4 + 1

            for x in range(0, 4):
                teams[key][x].team_number = initial + x
                teams[key][x].save()

                team_players_map[teams[key][x].team_number] = teams[key][x].pantheon_id

        number_of_teams = len(teams.keys())
        print("Number of teams: {}".format(number_of_teams))
        assert len(team_players_map.keys()) == confirm_players.count()

        with open(TeamSeating.initial_seating, "r") as f:
            initial_seating = f.read()

        rounds_text = initial_seating.splitlines()
        rounds = []
        for r in rounds_text:
            tables_text = r.split()
            tables = []

            for t in tables_text:
                players_ids = [int(x) for x in t.split("-")]
                assert len(players_ids) == 4

                # shuffle player winds
                random.shuffle(players_ids)

                tables.append(players_ids)

                teams_on_the_table = (
                    TournamentPlayers.objects.filter(tournament_id=settings.TOURNAMENT_ID, team_number__in=players_ids)
                    .values_list("team_name", flat=True)
                    .distinct()
                    .count()
                )

                # each table should contains players from different commands
                assert teams_on_the_table == 4

            assert number_of_teams == len(tables)

            rounds.append(tables)

        assert len(rounds) == 7

        data = {"team_players_map": team_players_map, "seating": rounds}

        with open(TeamSeating.processed_seating, "w") as f:
            f.write(json.dumps(data))

        print("Seating was saved to {}".format(TeamSeating.processed_seating))
