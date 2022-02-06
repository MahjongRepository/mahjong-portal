import json
import os.path
import random
import shutil
from os import listdir
from statistics import stdev

from django.conf import settings
from django.core.management.base import BaseCommand

NUMBER_OF_TEAMS = 26
ALL_SEATING_FOLDER = os.path.join(settings.BASE_DIR, "shared", "league_seating")


class Command(BaseCommand):
    def handle(self, *args, **options):
        seating_files = [f for f in listdir(ALL_SEATING_FOLDER)]
        seating_data = []
        for seating_file in seating_files:
            with open(os.path.join(ALL_SEATING_FOLDER, seating_file)) as f:
                seating_data.append(json.loads(f.read()))

        print(f"total seating: {len(seating_data)}")
        best_seating = sorted(seating_data, key=lambda x: (x["max_min_difference"], x["stdev"]))[0]
        print(f"max-min: {best_seating['max_min_difference']}")
        print(f"stdev: {best_seating['stdev']:.4f}")

        team_intersections_matrix = [[0 for _ in range(NUMBER_OF_TEAMS)] for _ in range(NUMBER_OF_TEAMS)]

        for team_number in best_seating["teams_stat"].keys():
            for other_team_number in best_seating["teams_stat"][team_number]["played_against_other_teams"].keys():
                team_intersections_matrix[int(team_number)][int(other_team_number)] = best_seating["teams_stat"][
                    team_number
                ]["played_against_other_teams"][other_team_number]

        print("\n".join(["".join(["{:3}".format(item) for item in row]) for row in team_intersections_matrix]))
