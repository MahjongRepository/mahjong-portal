# -*- coding: utf-8 -*-
from player.tenhou.models import TenhouGameLog
from utils.tenhou.helper import (
    download_all_games_from_nodochi,
    recalculate_tenhou_statistics_for_four_players,
    save_played_games,
)


class TenhouHelper:

    @staticmethod
    def recalculate_tenhou_account(tenhou_object, current_time, with_pycurl=False):
        TenhouGameLog.objects.filter(tenhou_object=tenhou_object).delete()

        player_games, account_start_date, four_players_rate, is_active_account = download_all_games_from_nodochi(
            tenhou_object.tenhou_username, only_ranking_games=True, with_pycurl=with_pycurl
        )

        if is_active_account:
            tenhou_object.username_created_at = account_start_date
            save_played_games(tenhou_object, player_games)
            recalculate_tenhou_statistics_for_four_players(tenhou_object, player_games, four_players_rate, current_time)
        else:
            tenhou_object.is_active = False
            tenhou_object.is_main = False
            tenhou_object.save()
