from datetime import datetime

import pytz
from django.core.management.base import BaseCommand

from league.models import League, LeagueGame, LeagueGameSlot, LeagueSession, LeagueTeam

SEATING = """
3-12-17-23 5-6-11-18 4-16-20-22 7-13-15-24 2-14-19-21 1-8-9-10
2-4-7-11 10-22-23-24 1-12-14-18 6-9-13-19 3-8-16-21 5-15-17-20
2-6-20-24 10-17-18-19 5-7-12-16 3-9-14-22 11-15-21-23 1-4-8-13
7-9-20-23 8-15-19-22 4-14-17-24 6-10-12-21 11-13-16-18 1-2-3-5
10-11-14-20 1-16-19-23 3-4-15-18 5-9-21-24 2-12-13-22 6-7-8-17
1-17-21-22 8-11-12-24 3-7-19-20 2-9-18-23 4-5-10-13 6-14-15-16
4-9-12-15 1-6-7-22 2-10-16-17 13-18-20-21 3-11-19-24 5-8-14-23
"""


class Command(BaseCommand):
    def handle(self, *args, **options):
        league = League.objects.get(slug="yoroshiku-league-2")

        session_dates = [
            datetime(2023, 4, 1, 7, 0, tzinfo=pytz.UTC),
            datetime(2023, 4, 1, 13, 0, tzinfo=pytz.UTC),
            datetime(2023, 4, 15, 7, 0, tzinfo=pytz.UTC),
            datetime(2023, 4, 15, 13, 0, tzinfo=pytz.UTC),
            datetime(2023, 4, 29, 7, 0, tzinfo=pytz.UTC),
            datetime(2023, 4, 29, 13, 0, tzinfo=pytz.UTC),
            datetime(2023, 5, 13, 7, 0, tzinfo=pytz.UTC),
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
