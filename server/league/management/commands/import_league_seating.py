import json
import os.path
from datetime import datetime, timedelta
from os import listdir

import pytz
from django.conf import settings
from django.core.management.base import BaseCommand

from league.models import League, LeagueGame, LeagueGameSlot, LeaguePlayer, LeagueSession, LeagueTeam

NUMBER_OF_TEAMS = 26
ALL_SEATING_FOLDER = os.path.join(settings.BASE_DIR, "shared", "league_seating")


class Command(BaseCommand):
    def handle(self, *args, **options):
        league = League.objects.all().first()

        LeaguePlayer.objects.all().update(user=None)
        LeagueGameSlot.objects.all().delete()
        LeagueGame.objects.all().delete()
        LeagueSession.objects.all().delete()

        initial_sessions = [
            # 16-00 MSK
            datetime(2021, 2, 12, 13, 0, tzinfo=pytz.UTC),
            # 10-00 MSK
            datetime(2021, 2, 19, 7, 0, tzinfo=pytz.UTC),
            # 16-00 MSK
            datetime(2021, 2, 19, 13, 0, tzinfo=pytz.UTC),
        ]

        seating_files = [f for f in listdir(ALL_SEATING_FOLDER)]
        seating_data = []
        for seating_file in seating_files:
            with open(os.path.join(ALL_SEATING_FOLDER, seating_file)) as f:
                data = json.loads(f.read())
                data["file_name"] = seating_file
                seating_data.append(data)

        print(f"total seating: {len(seating_data)}")
        best_seating = sorted(seating_data, key=lambda x: (x["max_min_difference"], x["stdev"]))[0]
        print(f"file: {best_seating['file_name']}")
        print(f"max-min: {best_seating['max_min_difference']}")
        print(f"stdev: {best_seating['stdev']:.4f}")

        team_intersections_matrix = [[0 for _ in range(NUMBER_OF_TEAMS)] for _ in range(NUMBER_OF_TEAMS)]

        for team_number in best_seating["teams_stat"].keys():
            for other_team_number in best_seating["teams_stat"][team_number]["played_against_other_teams"].keys():
                team_intersections_matrix[int(team_number)][int(other_team_number)] = best_seating["teams_stat"][
                    team_number
                ]["played_against_other_teams"][other_team_number]

        print("\n".join(["".join(["{:3}".format(item) for item in row]) for row in team_intersections_matrix]))

        best_seating["sessions"] = sorted(best_seating["sessions"], key=lambda x: x["session_number"])
        for i, session in enumerate([x["session_tables"] for x in best_seating["sessions"]]):
            if i <= 2:
                start_time = initial_sessions[i]
            else:
                shift = i % 3
                start_time = initial_sessions[shift] + timedelta(days=int(((i - shift) / 3) * 2) * 7)

            session_obj = LeagueSession.objects.create(league=league, number=i, start_time=start_time)

            for table in session:
                for _ in range(2):
                    game = LeagueGame.objects.create(session=session_obj)
                    for team_position, team_number in enumerate(table):
                        LeagueGameSlot.objects.create(
                            position=team_position, game=game, team=LeagueTeam.objects.get(number=team_number)
                        )
