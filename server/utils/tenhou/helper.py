# -*- coding: utf-8 -*-
import hashlib

from django.db import transaction

from player.tenhou.models import TenhouStatistics, TenhouNickname
from utils.general import get_month_first_day, get_month_last_day
from utils.tenhou.current_tenhou_games import lobbies_dict
from utils.tenhou.points_calculator import PointsCalculator


def parse_log_line(line):
    """
    Example of the line:
    23:59 | 20 | 四般東喰赤－ | 最終回(+61.0) manyaoba(+1.0) 可以打(-19.0) KENT6MG(-43.0)
    """

    game_time = line[0:5]
    game_length = int(line[8:10])
    game_rules = line[13:19]
    players = line[22:len(line)]

    temp_players = players.split(' ')
    place = 1
    players = []
    for temp in temp_players:
        name = temp.split('(')[0]

        # iterate symbol by symbol from the end of string
        # and if it is open brace symbol
        # it means that everything before that brace
        # is player name
        for i in reversed(range(len(temp))):
            if temp[i] == '(':
                name = temp[0:i]
                break

        players.append({
            'name': name,
            'place': place,
        })

        place += 1

    return {
        'players': players,
        'game_rules': game_rules,
        'game_time': game_time,
        'game_length': game_length
    }


def recalculate_tenhou_statistics(tenhou_object, all_games=None):
    with transaction.atomic():
        games = tenhou_object.game_logs.all()

        lobbies_data = {
            TenhouStatistics.KYU_LOBBY: {
                'all': {'played_games': 0, 1: 0, 2: 0, 3: 0, 4: 0},
                'current_month': {'played_games': 0, 1: 0, 2: 0, 3: 0, 4: 0}
            },
            TenhouStatistics.DAN_LOBBY: {
                'all': {'played_games': 0, 1: 0, 2: 0, 3: 0, 4: 0},
                'current_month': {'played_games': 0, 1: 0, 2: 0, 3: 0, 4: 0}
            },
            TenhouStatistics.UPPERDAN_LOBBY: {
                'all': {'played_games': 0, 1: 0, 2: 0, 3: 0, 4: 0},
                'current_month': {'played_games': 0, 1: 0, 2: 0, 3: 0, 4: 0}
            },
            TenhouStatistics.PHOENIX_LOBBY: {
                'all': {'played_games': 0, 1: 0, 2: 0, 3: 0, 4: 0},
                'current_month': {'played_games': 0, 1: 0, 2: 0, 3: 0, 4: 0}
            },
        }

        for game in games:
            lobby_name = lobbies_dict[game.game_rules[1]]

            lobbies_data[lobby_name]['all']['played_games'] += 1
            lobbies_data[lobby_name]['all'][game.place] += 1

            month_first_day = get_month_first_day()
            month_last_day = get_month_last_day()

            if month_first_day <= game.game_date <= month_last_day:
                lobbies_data[lobby_name]['current_month']['played_games'] += 1
                lobbies_data[lobby_name]['current_month'][game.place] += 1

        total_played_games = 0
        total_first_place = 0
        total_second_place = 0
        total_third_place = 0
        total_fourth_place = 0

        month_played_games = 0
        month_first_place = 0
        month_second_place = 0
        month_third_place = 0
        month_fourth_place = 0

        TenhouStatistics.objects.filter(tenhou_object=tenhou_object).delete()

        for lobby_key, lobby_data in lobbies_data.items():
            stat_types = {
                'all': TenhouStatistics.ALL_TIME,
                'current_month': TenhouStatistics.CURRENT_MONTH,
            }

            for key, stat_type in stat_types.items():
                if lobby_data[key]['played_games']:
                    stat_object, _ = TenhouStatistics.objects.get_or_create(
                        lobby=lobby_key,
                        tenhou_object=tenhou_object,
                        stat_type=stat_type
                    )

                    games_count = lobby_data[key]['played_games']
                    first_place = lobby_data[key][1]
                    second_place = lobby_data[key][2]
                    third_place = lobby_data[key][3]
                    fourth_place = lobby_data[key][4]

                    if stat_type == TenhouStatistics.ALL_TIME:
                        total_played_games += games_count
                        total_first_place += first_place
                        total_second_place += second_place
                        total_third_place += third_place
                        total_fourth_place += fourth_place
                    else:
                        month_played_games += games_count
                        month_first_place += first_place
                        month_second_place += second_place
                        month_third_place += third_place
                        month_fourth_place += fourth_place

                    average_place = (first_place + second_place * 2 + third_place * 3 + fourth_place * 4) / games_count

                    first_place = (first_place / games_count) * 100
                    second_place = (second_place / games_count) * 100
                    third_place = (third_place / games_count) * 100
                    fourth_place = (fourth_place / games_count) * 100

                    stat_object.played_games = games_count
                    stat_object.average_place = average_place
                    stat_object.first_place = first_place
                    stat_object.second_place = second_place
                    stat_object.third_place = third_place
                    stat_object.fourth_place = fourth_place
                    stat_object.save()

        if total_played_games:
            total_average_place = (total_first_place + total_second_place * 2 + total_third_place * 3 + total_fourth_place * 4) / total_played_games
        else:
            total_average_place = 0

        if month_played_games:
            month_average_place = (month_first_place + month_second_place * 2 + month_third_place * 3 + month_fourth_place * 4) / month_played_games
        else:
            month_average_place = 0

        rank = PointsCalculator.calculate_rank(games)

        # some players are play sanma only
        # or in custom lobby only
        # we still need to keep for them last played date
        if all_games:
            last_played_date = all_games and all_games[-1]['game_date'] or None
        else:
            last_played_date = games.exists() and games.last().game_date or None

        rank = [x[0] for x in TenhouNickname.RANKS if x[1] == rank['rank']][0]
        # 3 or less dan
        if rank <= 12:
            # we need to erase user rate when user lost 4 dan
            tenhou_object.four_games_rate = 0

        tenhou_object.rank = rank
        tenhou_object.pt = rank['pt']
        tenhou_object.end_pt = rank['end_pt']
        tenhou_object.last_played_date = last_played_date
        tenhou_object.played_games = total_played_games
        tenhou_object.average_place = total_average_place
        tenhou_object.month_played_games = month_played_games
        tenhou_object.month_average_place = month_average_place
        tenhou_object.save()
