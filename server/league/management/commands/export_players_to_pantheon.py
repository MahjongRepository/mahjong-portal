# -*- coding: utf-8 -*-

from time import sleep

import requests
from django.conf import settings
from django.core.management.base import BaseCommand

from league.models import League, LeaguePlayer
from utils.general import make_random_letters_and_digit_string


class Command(BaseCommand):
    def handle(self, *args, **options):
        league = League.objects.get(slug="yoroshiku-league-2")
        players_to_export = LeaguePlayer.objects.filter(team__league=league).exclude(user__isnull=True)

        team_names = {}
        for player in players_to_export:
            team_names[player.user.new_pantheon_id] = player.team.name
            try:
                self.add_user_to_pantheon(player.user.new_pantheon_id)
            except Exception:
                pass
            sleep(0.2)

        self.update_users_teams(team_names)

    def update_users_teams(self, team_names):
        self.send_request_to_pantheon(
            "updatePlayersTeams", {"eventId": settings.LEAGUE_PANTHEON_EVENT_ID, "teamNameMap": team_names}
        )

    def add_user_to_pantheon(self, player_pantheon_id):
        self.send_request_to_pantheon(
            "registerPlayerCP", {"eventId": settings.LEAGUE_PANTHEON_EVENT_ID, "playerId": player_pantheon_id}
        )

    def send_request_to_pantheon(self, method, params):
        cookies = {"pantheon_authToken": settings.PANTHEON_ADMIN_COOKIE}
        headers = {
            "X-Auth-Token": settings.PANTHEON_ADMIN_COOKIE,
            "X-Current-Event-Id": settings.LEAGUE_PANTHEON_EVENT_ID,
            "X-Current-Person-Id": settings.PANTHEON_ADMIN_ID,
        }

        data = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": make_random_letters_and_digit_string(),
        }

        response = requests.post(settings.PANTHEON_NEW_API_URL, json=data, headers=headers, cookies=cookies)
        if response.status_code == 500:
            raise Exception("Register player. 500 response")

        content = response.json()
        if content.get("error"):
            raise Exception("Register player. Pantheon error: {}".format(content.get("error")))

        return response.json()
