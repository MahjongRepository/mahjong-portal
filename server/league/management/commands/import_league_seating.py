from datetime import datetime

import pytz
from django.core.management.base import BaseCommand

from league.models import League, LeagueGame, LeagueGameSlot, LeagueSession, LeagueTeam

SEATING = """
7-10-12-20 4-16-17-23 3-18-22-24 5-6-9-19 2-8-13-15 1-11-14-21
9-11-12-24 2-18-20-21 1-3-7-23 6-8-14-17 13-16-19-22 4-5-10-15
1-10-17-24 2-5-12-16 6-7-21-22 11-13-20-23 9-14-15-18 3-4-8-19
5-7-13-14 19-21-23-24 8-11-16-18 4-9-20-22 2-3-6-10 1-12-15-17
6-12-18-23 2-4-14-24 3-15-16-21 8-10-11-22 7-9-13-17 1-5-19-20
6-16-20-24 3-5-11-17 14-15-22-23 4-12-13-21 7-10-18-19 1-2-8-9
3-12-14-20 5-8-21-24 2-17-19-22 6-7-11-15 9-10-16-23 1-4-13-18
"""


class Command(BaseCommand):
    def handle(self, *args, **options):
        league = League.objects.get(slug="yoroshiku-league-2")

        session_dates = [
            datetime(2023, 5, 13, 13, 0, tzinfo=pytz.UTC),
            datetime(2023, 5, 27, 7, 0, tzinfo=pytz.UTC),
            datetime(2023, 5, 27, 13, 0, tzinfo=pytz.UTC),
            datetime(2023, 6, 10, 7, 0, tzinfo=pytz.UTC),
            datetime(2023, 6, 10, 13, 0, tzinfo=pytz.UTC),
            datetime(2023, 6, 17, 7, 0, tzinfo=pytz.UTC),
            datetime(2023, 6, 17, 13, 0, tzinfo=pytz.UTC),
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

            session_number = created_sessions + i + 1
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
