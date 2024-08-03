# -*- coding: utf-8 -*-

from time import sleep

from django.core.management.base import BaseCommand
from django.utils import timezone

from player.tenhou.models import TenhouGameLog, TenhouNickname
from utils.tenhou.helper import (
    download_all_games_from_nodochi,
    recalculate_tenhou_statistics_for_four_players,
    save_played_games,
)


def get_date_string():
    return timezone.now().strftime("%H:%M:%S")


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--nickname", default=None, type=str)

    def handle(self, *args, **options):
        tenhou_nickname = options.get("nickname")
        print("{0}: Start".format(get_date_string()))

        if tenhou_nickname:
            tenhou_objects = TenhouNickname.objects.filter(is_active=True, tenhou_username=tenhou_nickname)
        else:
            tenhou_objects = TenhouNickname.objects.filter(is_active=True)
        tenhou_players_count = len(tenhou_objects)
        current_player_index = 1
        for tenhou_object in tenhou_objects:
            print(f"[{current_player_index}/{tenhou_players_count}] Processing {tenhou_object.tenhou_username}")

            TenhouGameLog.objects.filter(tenhou_object=tenhou_object).delete()

            player_games, account_start_date, four_players_rate = download_all_games_from_nodochi(
                tenhou_object.tenhou_username, only_ranking_games=True
            )

            tenhou_object.username_created_at = account_start_date

            save_played_games(tenhou_object, player_games)

            recalculate_tenhou_statistics_for_four_players(tenhou_object, player_games, four_players_rate)
            current_player_index = current_player_index + 1

            # let's be gentle and don't ddos nodochi
            sleep(10)

        print("{0}: End".format(get_date_string()))
