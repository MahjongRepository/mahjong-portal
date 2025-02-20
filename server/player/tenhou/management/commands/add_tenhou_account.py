# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.utils import timezone

from player.models import Player
from player.tenhou.models import TenhouNickname
from utils.tenhou.helper import (
    download_all_games_from_nodochi,
    recalculate_tenhou_statistics_for_four_players,
    save_played_games,
)


def get_date_string():
    return timezone.now().strftime("%H:%M:%S")


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("player_name", type=str)
        parser.add_argument("tenhou_nickname", type=str)

    def handle(self, *args, **options):
        print("{0}: Start".format(get_date_string()))

        temp = options.get("player_name").split(" ")
        last_name = temp[0]
        first_name = temp[1]

        player = Player.objects.get(first_name_ru=first_name, last_name_ru=last_name)
        tenhou_nickname = options.get("tenhou_nickname")

        player_games, account_start_date, four_players_rate = download_all_games_from_nodochi(tenhou_nickname)

        if not player_games:
            print("Not correct account")
            return

        is_main = TenhouNickname.active_objects.filter(player=player, is_active=True).count() == 0
        tenhou_object = TenhouNickname.active_objects.create(
            is_main=is_main, player=player, tenhou_username=tenhou_nickname, username_created_at=account_start_date
        )

        save_played_games(tenhou_object, player_games)

        recalculate_tenhou_statistics_for_four_players(tenhou_object, player_games, four_players_rate)

        print("{0}: End".format(get_date_string()))
