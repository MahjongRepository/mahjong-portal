from datetime import datetime

import pytz
from django.core.management.base import BaseCommand

from league.models import League, LeagueGame, LeagueGameSlot, LeagueSession, LeagueTeam

SEATING = """
6-11-14-15 10-12-19-22 5-8-13-16 1-2-17-24 7-18-21-23 3-4-9-20
16-17-19-21 2-3-7-10 8-14-22-24 13-15-20-23 9-11-12-18 1-4-5-6
5-12-23-24 2-9-15-16 7-13-14-19 6-17-20-22 1-10-11-21 3-4-8-18
5-7-9-22 2-6-18-19 4-13-21-24 8-10-15-17 3-11-16-23 1-12-14-20
3-12-13-17 4-15-18-22 6-10-16-24 7-8-11-20 1-9-19-23 2-5-14-21
5-10-18-20 4-14-17-23 6-8-9-21 3-15-19-24 2-11-13-22 1-7-12-16
9-10-13-14 5-11-17-19 2-8-12-23 16-18-20-24 1-3-21-22 4-6-7-15
"""


class Command(BaseCommand):
    def handle(self, *args, **options):
        league = League.objects.get(slug="yoroshiku-league-2")

        session_dates = [
            datetime(2022, 12, 24, 7, 0, tzinfo=pytz.UTC),
            datetime(2022, 12, 24, 13, 0, tzinfo=pytz.UTC),
            datetime(2023, 1, 7, 7, 0, tzinfo=pytz.UTC),
            datetime(2023, 1, 7, 13, 0, tzinfo=pytz.UTC),
            datetime(2023, 1, 21, 7, 0, tzinfo=pytz.UTC),
            datetime(2023, 1, 21, 13, 0, tzinfo=pytz.UTC),
            datetime(2023, 2, 4, 7, 0, tzinfo=pytz.UTC),
        ]

        seating = SEATING.strip().splitlines()
        seating = [x.split() for x in seating]
        seating = [[x.split("-") for x in y] for y in seating]

        created_sessions = LeagueSession.objects.filter(league=league).count()

        for i, session in enumerate(seating):
            start_time = session_dates[i]

            for table in session:
                assert len(table) == 4
                assert len(set(table)) == len(table), "Duplicate team in table"

            session_number = created_sessions + i
            session_obj = LeagueSession.objects.create(
                status=LeagueSession.NEW, league=league, number=session_number, start_time=start_time
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
