from datetime import datetime

import pytz
from django.core.management.base import BaseCommand

from league.models import League, LeagueGame, LeagueGameSlot, LeagueSession, LeagueTeam

SEATING = """
4-14-17-21 3-5-16-18 9-12-15-24 2-19-20-22 1-11-13-23 6-7-8-10
8-12-20-23 7-17-18-22 6-16-21-24 1-2-4-5 11-14-15-19 3-9-10-13
9-21-22-23 5-10-17-20 3-4-11-12 7-13-16-19 1-14-18-24 2-6-8-15
4-10-18-23 3-6-17-19 12-13-14-22 2-7-11-24 1-9-16-20 5-8-15-21
3-7-20-21 5-19-23-24 2-12-16-17 1-8-11-22 4-13-15-18 6-9-10-14
8-13-17-24 2-3-14-23 6-11-18-20 1-12-19-21 10-15-16-22 4-5-7-9
1-3-15-17 8-9-18-19 4-20-22-24 5-6-12-13 7-14-16-23 2-10-11-21
"""


class Command(BaseCommand):
    def handle(self, *args, **options):
        league = League.objects.get(slug="yoroshiku-league-2")

        session_dates = [
            datetime(2022, 10, 15, 13, 0, tzinfo=pytz.UTC),
            datetime(2022, 10, 29, 7, 0, tzinfo=pytz.UTC),
            datetime(2022, 10, 29, 13, 0, tzinfo=pytz.UTC),
            datetime(2022, 11, 19, 7, 0, tzinfo=pytz.UTC),
            datetime(2022, 11, 19, 13, 0, tzinfo=pytz.UTC),
            datetime(2022, 12, 10, 7, 0, tzinfo=pytz.UTC),
            datetime(2022, 12, 10, 13, 0, tzinfo=pytz.UTC),
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
