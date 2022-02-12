import os.path

import requests
from django.conf import settings
from django.core.management.base import BaseCommand

from league.models import LeagueGameSlot, LeaguePlayer
from utils.general import make_random_letters_and_digit_string

NUMBER_OF_TEAMS = 26
ALL_SEATING_FOLDER = os.path.join(settings.BASE_DIR, "shared", "league_seating")


class Command(BaseCommand):
    def handle(self, *args, **options):
        assigned_player_ids = (
            LeagueGameSlot.objects.exclude(assigned_player=None).values("assigned_player_id").distinct()
        )
        players_to_export = LeaguePlayer.objects.filter(id__in=assigned_player_ids)

        # team_names = {}
        for player in players_to_export:
            # team_names[player.user.new_pantheon_id] = player.team.name
            # self.add_user_to_pantheon(player.user.new_pantheon_id)
            print(player.team.name, player.name, player.user.email, player.user.new_pantheon_id)
        #
        # data = {
        #     "jsonrpc": "2.0",
        #     "method": "updatePlayersTeams",
        #     "params": {"eventId": settings.LEAGUE_PANTHEON_EVENT_ID, "teamNameMap": team_names},
        #     "id": make_random_letters_and_digit_string(),
        # }
        #
        # headers = {"X-Internal-Query-Secret": settings.PANTHEON_ADMIN_TOKEN}
        #
        # response = requests.post(settings.PANTHEON_NEW_API_URL, json=data, headers=headers)
        # if response.status_code == 500:
        #     raise Exception("Add teams. Pantheon 500 error")
        #
        # content = response.json()
        # if content.get("error"):
        #     raise Exception(f"Pantheon {content.get('error')} error")

    def add_user_to_pantheon(self, player_pantheon_id):
        headers = {"X-Internal-Query-Secret": settings.PANTHEON_ADMIN_TOKEN}
        data = {
            "jsonrpc": "2.0",
            "method": "registerPlayerCP",
            "params": {"eventId": settings.LEAGUE_PANTHEON_EVENT_ID, "playerId": player_pantheon_id},
            "id": make_random_letters_and_digit_string(),
        }

        response = requests.post(settings.PANTHEON_NEW_API_URL, json=data, headers=headers)
        if response.status_code == 500:
            raise Exception("Register player. 500 response")

        content = response.json()
        if content.get("error"):
            raise Exception("Register player. Pantheon error: {}".format(content.get("error")))
