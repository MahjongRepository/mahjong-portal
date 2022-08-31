import csv

from django.core.management.base import BaseCommand

from league.models import League, LeaguePlayer, LeagueTeam


class Command(BaseCommand):
    def handle(self, *args, **options):
        with open("league_teams.csv", "r") as f:
            records = list(csv.DictReader(f))

        league = League.objects.get(slug="yoroshiku-league-2")

        LeaguePlayer.objects.filter(team__league=league).delete()
        LeagueTeam.objects.filter(league=league).delete()

        team_names = sorted(list(set([x["team"] for x in records])))
        team_objects = {}
        for i, team_name in enumerate(team_names):
            team_objects[team_name] = LeagueTeam.objects.create(name=team_name, league=league, number=i + 1)

        for record in records:
            LeaguePlayer.objects.create(
                name=record["name"], team=team_objects[record["team"]], tenhou_nickname=record["nick"]
            )
