from statistics import stdev

from django.core.management.base import BaseCommand

NUMBER_OF_TEAMS = 26
NUMBER_OF_UNIQUE_SESSIONS = 13


class Command(BaseCommand):
    """
    It was tested only for 26 teams, for any other number of team it should be adjusted
    """

    def handle(self, *args, **options):
        teams_stat = {}
        for team_number in range(NUMBER_OF_TEAMS):
            teams_stat[team_number] = {"played_sessions": 0, "played_against_other_teams": {}}

            for other_team_number in range(NUMBER_OF_TEAMS):
                if other_team_number == team_number:
                    continue
                teams_stat[team_number]["played_against_other_teams"][other_team_number] = 0

        first_session_tables = self._play_session()
        second_session_tables = self._play_session()

        all_sessions = first_session_tables + second_session_tables
        assert len(all_sessions) == NUMBER_OF_UNIQUE_SESSIONS * 2, "wrong number of played sessions"

        self._calculate_teams_stat(all_sessions, teams_stat)

        number_of_played_sessions = list(set([x["played_sessions"] for x in teams_stat.values()]))
        assert len(number_of_played_sessions) == 1, "all teams should play same number of sessions"

        played_against_other_team_session_numbers = []
        for team_number in range(NUMBER_OF_TEAMS):
            played_against_other_team_session_numbers.extend(
                teams_stat[team_number]["played_against_other_teams"].values()
            )

        print(
            f"Sessions played per team: {number_of_played_sessions[0]}, (games per team {number_of_played_sessions[0] * 2})"
        )
        print(f"Number of played weeks (3 sessions per two weeks): {int((number_of_played_sessions[0] / 3) * 2)}")
        print(f"Min sessions intersection between teams: {min(played_against_other_team_session_numbers)}")
        print(f"Max sessions intersection between teams: {max(played_against_other_team_session_numbers)}")
        print(f"Standard deviation: {stdev(played_against_other_team_session_numbers):.4f}")

        for i, session in enumerate(all_sessions):
            tables_str = []
            for table in session:
                tables_str.append("-".join([str(x) for x in table]))
            print(f"Session: #{i + 1}")
            print(" ".join(tables_str))

    def _play_session(self):
        all_tables = []
        for session_number in range(NUMBER_OF_UNIQUE_SESSIONS):
            skipped_teams_in_session = [(session_number * 2), (session_number * 2) + 1]
            playing_this_session_teams = [x for x in range(NUMBER_OF_TEAMS) if x not in skipped_teams_in_session]
            assert len(playing_this_session_teams) == 24

            session_tables = []
            for i in range(0, len(playing_this_session_teams), 4):
                session_tables.append(playing_this_session_teams[i : i + 4])

            all_tables.append(session_tables)
        return all_tables

    def _calculate_teams_stat(self, sessions, teams_stat):
        for session in sessions:
            for table in session:
                for team_number in table:
                    teams_stat[team_number]["played_sessions"] += 1

                    for other_team_number in table:
                        if other_team_number == team_number:
                            continue

                        teams_stat[team_number]["played_against_other_teams"][other_team_number] += 1
