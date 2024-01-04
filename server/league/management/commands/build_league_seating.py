import os.path
import random
import shutil
from statistics import stdev

import ujson as json
from django.conf import settings
from django.core.management.base import BaseCommand

NUMBER_OF_TEAMS = 26
NUMBER_OF_UNIQUE_SESSIONS = 13
INITIAL_SEATING_ITERATIONS = 10000000
IMPROVE_SEATING_ITERATIONS = 50

ALL_SEATING_FOLDER = os.path.join(settings.BASE_DIR, "shared", "league_seating")


class Command(BaseCommand):
    """
    It was tested only for 26 teams, for any other number of team it should be adjusted
    """

    def handle(self, *args, **options):
        if os.path.exists(ALL_SEATING_FOLDER):
            shutil.rmtree(ALL_SEATING_FOLDER)
        os.mkdir(ALL_SEATING_FOLDER)

        for i in range(INITIAL_SEATING_ITERATIONS):
            if (i + 1) % 1000 == 0:
                print(f"Iteration {i + 1}/{INITIAL_SEATING_ITERATIONS}")

            seating = {
                "max_min_difference": 100,
                "stdev": 100,
                "sessions": [],
                "teams_stat": {},
            }

            first_session_tables = self._play_session(0)
            second_session_tables = self._play_session(13)

            all_sessions = first_session_tables + second_session_tables
            assert len(all_sessions) == NUMBER_OF_UNIQUE_SESSIONS * 2, "wrong number of played sessions"
            seating["sessions"] = all_sessions

            self._calculate_seating_teams_stat(seating)

            if seating["max_min_difference"] <= 6:
                self._minimize_team_intersections(seating)

                number_of_played_sessions = list(set([x["played_sessions"] for x in seating["teams_stat"].values()]))
                assert len(number_of_played_sessions) == 1, "all teams should play same number of sessions"

                with open(os.path.join(ALL_SEATING_FOLDER, f"{i}.json"), "w") as f:
                    f.write(json.dumps(seating))

    def _play_session(self, shift):
        all_tables = []
        for session_number in range(NUMBER_OF_UNIQUE_SESSIONS):
            skipped_teams_in_session = [(session_number * 2), (session_number * 2) + 1]
            playing_this_session_teams = [x for x in range(NUMBER_OF_TEAMS) if x not in skipped_teams_in_session]
            assert len(playing_this_session_teams) == 24

            session_tables = []
            random.shuffle(playing_this_session_teams)
            for i in range(0, len(playing_this_session_teams), 4):
                session_tables.append(playing_this_session_teams[i : i + 4])

            all_tables.append(
                {
                    "session_number": session_number + shift,
                    "session_tables": session_tables,
                }
            )

        return all_tables

    def _calculate_seating_teams_stat(self, seating):
        for team_number in range(NUMBER_OF_TEAMS):
            seating["teams_stat"][team_number] = {"played_sessions": 0, "played_against_other_teams": {}}

            for other_team_number in range(NUMBER_OF_TEAMS):
                if other_team_number == team_number:
                    continue
                seating["teams_stat"][team_number]["played_against_other_teams"][other_team_number] = 0

        for session in [x["session_tables"] for x in seating["sessions"]]:
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
        return played_against_other_team_session_numbers

    def _minimize_team_intersections(self, seating):
        # Algorithm:
        # 1. Iterate over each team.
        # 2. Find which teams has minimum and maximum number of intersections with the current one.
        # 3. Iterate over each round.
        # 4. Check if in the given round current team plays with the team of maximum intersections.
        #    If true, then check if there exists a pair of tables with 8 unique team, including table
        #    with our team + teamMAX and table with teamMIN.
        #    If true, swap players from teamMAX and teamMIN.
        #    If any condition is not true, go to the next round.
        # 5. Proceed to the next team.
        # 6. Recalculate intersections and repeat algorithm, until we have minimized the maximum.

        current_iteration = 0

        while current_iteration < IMPROVE_SEATING_ITERATIONS:
            team_intersections_matrix = [[0 for _ in range(NUMBER_OF_TEAMS)] for _ in range(NUMBER_OF_TEAMS)]

            for team_number in seating["teams_stat"].keys():
                for other_team_number in seating["teams_stat"][team_number]["played_against_other_teams"].keys():
                    team_intersections_matrix[int(team_number)][int(other_team_number)] = seating["teams_stat"][
                        team_number
                    ]["played_against_other_teams"][other_team_number]

            played_against_other_team_session_numbers = []
            for team_number in range(NUMBER_OF_TEAMS):
                played_against_other_team_session_numbers.extend(
                    seating["teams_stat"][team_number]["played_against_other_teams"].values()
                )

            max_num_team_intersections = max(played_against_other_team_session_numbers)
            min_num_team_intersections = min(played_against_other_team_session_numbers)

            if max_num_team_intersections == 1:
                break

            swaps_done = 0

            for team in range(0, NUMBER_OF_TEAMS):
                comp_team = 1 if team == 0 else 0

                max_intr = team_intersections_matrix[team][comp_team]
                min_intr = team_intersections_matrix[team][comp_team]

                max_intr_team = comp_team
                min_intr_team = comp_team

                for __team in range(0, NUMBER_OF_TEAMS):
                    if team == __team:
                        continue

                    num_intr = team_intersections_matrix[team][__team]

                    if num_intr >= max_intr:
                        max_intr_team = __team
                        max_intr = num_intr

                    if team_intersections_matrix[team][__team] <= min_intr:
                        min_intr_team = __team
                        min_intr = num_intr

                # on each iteration we only deal with teams who make our maximum
                if max_intr != max_num_team_intersections:
                    continue

                randomly_shuffled_rounds = seating["sessions"]
                random.shuffle(randomly_shuffled_rounds)

                for r in [x["session_tables"] for x in randomly_shuffled_rounds]:
                    table_with_max = None
                    table_with_min = None
                    for t in r:
                        if team in t and max_intr_team in t:
                            table_with_max = t

                        if team not in t and min_intr_team in t:
                            table_with_min = t

                    if table_with_min is not None and table_with_max is not None:
                        table_with_max.remove(max_intr_team)
                        table_with_max.append(min_intr_team)
                        table_with_min.remove(min_intr_team)
                        table_with_min.append(max_intr_team)

                        new_numbers = self._calculate_seating_teams_stat(seating)

                        if (
                            max(new_numbers) > max_num_team_intersections
                            or min(new_numbers) < min_num_team_intersections
                        ):
                            # revert bad swapping
                            table_with_min.remove(max_intr_team)
                            table_with_min.append(min_intr_team)
                            table_with_max.remove(min_intr_team)
                            table_with_max.append(max_intr_team)
                        else:
                            max_num_team_intersections = max(new_numbers)
                            min_num_team_intersections = min(new_numbers)
                            swaps_done += 1
                            break

            # No more swaps can be done
            if swaps_done == 0:
                break

            current_iteration += 1

            # Reached maximum iterations during team intersections minimization
            if current_iteration == IMPROVE_SEATING_ITERATIONS:
                self._calculate_seating_teams_stat(seating)

        return seating
