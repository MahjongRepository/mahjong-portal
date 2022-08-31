from datetime import datetime, timedelta

import pytz
from django.core.management.base import BaseCommand

from league.models import League, LeagueGame, LeagueGameSlot, LeagueSession, LeagueTeam

NUMBER_OF_TEAMS = 26
SEATING = """
1-2-8-15 22-14-20-5 23-19-3-10 4-24-6-18 7-9-11-12 13-21-16-17
1-3-9-16 22-8-21-6 23-20-4-11 5-7-24-19 2-10-12-13 14-15-17-18
1-4-10-17 22-9-15-24 23-21-5-12 6-2-7-20 3-14-11-13 8-19-16-18
1-5-11-18 22-10-16-7 23-15-6-13 24-3-2-21 4-14-8-12 9-19-20-17
1-6-12-19 22-11-17-2 23-16-24-14 7-4-3-15 5-8-9-13 10-20-21-18
1-5-13-20 22-12-18-3 23-17-7-8 2-5-4-16 6-14-9-10 11-19-21-15
1-7-14-21 22-13-19-4 23-18-2-9 3-6-5-17 24-8-10-11 12-20-15-16
"""


class Command(BaseCommand):
    def handle(self, *args, **options):
        league = League.objects.get(slug="yoroshiku-league-2")

        LeagueGameSlot.objects.filter(team__league=league).delete()
        LeagueGame.objects.filter(session__league=league).delete()
        LeagueSession.objects.filter(league=league).delete()

        initial_sessions = [
            # 10-00 MSK
            datetime(2022, 9, 3, 7, 0, tzinfo=pytz.UTC),
            # 16-00 MSK
            datetime(2022, 9, 3, 13, 0, tzinfo=pytz.UTC),
        ]

        seating = SEATING.strip().splitlines()
        seating = [x.split() for x in seating]
        seating = [[x.split("-") for x in y] for y in seating]

        for i, session in enumerate(seating):
            if i <= 1:
                start_time = initial_sessions[i]
            else:
                shift = i % 2
                start_time = initial_sessions[shift] + timedelta(days=int(((i - shift) / 3) * 2) * 14)

            session_obj = LeagueSession.objects.create(
                status=LeagueSession.NEW, league=league, number=i, start_time=start_time
            )

            for table in session:
                for _ in range(2):
                    game = LeagueGame.objects.create(session=session_obj)
                    for team_position, team_number in enumerate(table):
                        LeagueGameSlot.objects.create(
                            position=team_position,
                            game=game,
                            team=LeagueTeam.objects.get(league=league, number=team_number),
                        )
