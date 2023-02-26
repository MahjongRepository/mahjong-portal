from datetime import datetime

import pytz
from django.core.management.base import BaseCommand

from league.models import League, LeagueGame, LeagueGameSlot, LeagueSession, LeagueTeam

SEATING = """
2-9-10-18 6-8-13-14 1-5-7-19 3-11-15-22 4-16-17-24 12-20-21-23
8-15-17-23 1-4-9-11 5-13-18-22 14-19-21-24 2-3-16-20 6-7-10-12
2-7-17-22 3-6-18-24 1-10-14-15 4-12-13-19 5-9-16-23 8-11-20-21
5-11-12-24 9-13-15-20 10-16-19-22 2-4-6-23 1-17-18-21 3-7-8-14
2-15-19-24 7-13-16-21 11-14-18-23 1-6-20-22 3-9-12-17 4-5-8-10
4-7-18-20 1-8-12-16 3-10-13-23 6-11-17-19 2-5-15-21 9-14-22-24
5-14-17-20 1-2-11-13 12-15-16-18 3-4-21-22 6-8-9-19 7-10-23-24
"""


class Command(BaseCommand):
    def handle(self, *args, **options):
        league = League.objects.get(slug="yoroshiku-league-2")

        session_dates = [
            datetime(2023, 2, 4, 13, 0, tzinfo=pytz.UTC),
            datetime(2023, 2, 18, 7, 0, tzinfo=pytz.UTC),
            datetime(2023, 2, 18, 13, 0, tzinfo=pytz.UTC),
            datetime(2023, 3, 4, 7, 0, tzinfo=pytz.UTC),
            datetime(2023, 3, 4, 13, 0, tzinfo=pytz.UTC),
            datetime(2023, 3, 18, 7, 0, tzinfo=pytz.UTC),
            datetime(2023, 3, 18, 13, 0, tzinfo=pytz.UTC),
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
