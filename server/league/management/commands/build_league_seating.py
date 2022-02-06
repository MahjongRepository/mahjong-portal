import json
import os.path
import random
from statistics import stdev

from django.conf import settings
from django.core.management.base import BaseCommand

NUMBER_OF_TEAMS = 26
NUMBER_OF_UNIQUE_SESSIONS = 13
ITERATIONS = 10000
ALL_SEATING_FILE = os.path.join(settings.BASE_DIR, "league_seating.json")


class Command(BaseCommand):
    """
    It was tested only for 26 teams, for any other number of team it should be adjusted
    """

    def handle(self, *args, **options):

        for i in range(ITERATIONS):
            print(f"Iteration {i + 1}/{ITERATIONS}")
            seating = {
                "max_min_difference": None,
                "stdev": None,
                "sessions": [],
                "teams_stat": {},
            }

            for team_number in range(NUMBER_OF_TEAMS):
                seating["teams_stat"][team_number] = {"played_sessions": 0, "played_against_other_teams": {}}

                for other_team_number in range(NUMBER_OF_TEAMS):
                    if other_team_number == team_number:
                        continue
                    seating["teams_stat"][team_number]["played_against_other_teams"][other_team_number] = 0

            first_session_tables = self._play_session()
            second_session_tables = self._play_session()

            all_sessions = first_session_tables + second_session_tables
            assert len(all_sessions) == NUMBER_OF_UNIQUE_SESSIONS * 2, "wrong number of played sessions"
            seating["sessions"] = all_sessions

            self._calculate_seating_teams_stat(seating)

            if seating["max_min_difference"] <= 7:
                self._print_stat(seating)

                with open(ALL_SEATING_FILE, "r") as f:
                    data = json.loads(f.read())

                data["data"].append(seating)

                with open(ALL_SEATING_FILE, "w") as f:
                    f.write(json.dumps(data))

    def _print_stat(self, seating):
        number_of_played_sessions = list(set([x["played_sessions"] for x in seating["teams_stat"].values()]))
        assert len(number_of_played_sessions) == 1, "all teams should play same number of sessions"

        played_against_other_team_session_numbers = []
        for team_number in range(NUMBER_OF_TEAMS):
            played_against_other_team_session_numbers.extend(
                seating["teams_stat"][team_number]["played_against_other_teams"].values()
            )

        print(
            f"sessions played per team: {number_of_played_sessions[0]} (games per team {number_of_played_sessions[0] * 2})"
        )
        print(f"max-min: {seating['max_min_difference']}")
        print(f"stdev: {seating['stdev']:.4f}")
        # for i, session in enumerate(seating["sessions"]):
        #     tables_str = []
        #     for table in session:
        #         tables_str.append("-".join([str(x) for x in table]))
        #     print(f"Session: #{i + 1}")
        #     print(" ".join(tables_str))

    def _play_session(self):
        all_tables = []
        for session_number in range(NUMBER_OF_UNIQUE_SESSIONS):
            skipped_teams_in_session = [(session_number * 2), (session_number * 2) + 1]
            playing_this_session_teams = [x for x in range(NUMBER_OF_TEAMS) if x not in skipped_teams_in_session]
            assert len(playing_this_session_teams) == 24

            random.shuffle(playing_this_session_teams)

            session_tables = []
            for i in range(0, len(playing_this_session_teams), 4):
                session_tables.append(playing_this_session_teams[i : i + 4])

            all_tables.append(session_tables)
        return all_tables

    def _calculate_seating_teams_stat(self, seating):
        for session in seating["sessions"]:
            for table in session:
                for team_number in table:
                    seating["teams_stat"][team_number]["played_sessions"] += 1

                    for other_team_number in table:
                        if other_team_number == team_number:
                            continue

                        seating["teams_stat"][team_number]["played_against_other_teams"][other_team_number] += 1

        played_against_other_team_session_numbers = []
        for team_number in range(NUMBER_OF_TEAMS):
            played_against_other_team_session_numbers.extend(
                seating["teams_stat"][team_number]["played_against_other_teams"].values()
            )

        seating["max_min_difference"] = max(played_against_other_team_session_numbers) - min(
            played_against_other_team_session_numbers
        )
        seating["stdev"] = stdev(played_against_other_team_session_numbers)
