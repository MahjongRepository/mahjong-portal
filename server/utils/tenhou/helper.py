# -*- coding: utf-8 -*-
from datetime import datetime
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup
from django.db import transaction

from player.tenhou.models import TenhouAggregatedStatistics, TenhouGameLog, TenhouStatistics
from utils.general import get_month_first_day, get_month_last_day
from utils.tenhou.current_tenhou_games import lobbies_dict
from utils.tenhou.points_calculator import FourPlayersPointsCalculator


def parse_log_line(line):
    """
    Example of the line:
    23:59 | 20 | 四般東喰赤－ | 最終回(+61.0) manyaoba(+1.0) 可以打(-19.0) KENT6MG(-43.0)
    """

    game_time = line[0:5]
    game_length = int(line[8:10])
    game_rules = line[13:19]
    players = line[22 : len(line)]

    temp_players = players.split(" ")
    place = 1
    players = []
    for temp in temp_players:
        name = temp.split("(")[0]

        # iterate symbol by symbol from the end of string
        # and if it is open brace symbol
        # it means that everything before that brace
        # is player name
        for i in reversed(range(len(temp))):
            if temp[i] == "(":
                name = temp[0:i]
                break

        players.append({"name": name, "place": place})

        place += 1

    return {"players": players, "game_rules": game_rules, "game_time": game_time, "game_length": game_length}


def recalculate_tenhou_statistics_for_four_players(tenhou_object, all_games=None):
    with transaction.atomic():
        games = tenhou_object.game_logs.filter(game_players=TenhouGameLog.FOUR_PLAYERS)

        lobbies_data = {
            TenhouStatistics.KYU_LOBBY: {
                "all": {"played_games": 0, 1: 0, 2: 0, 3: 0, 4: 0},
                "current_month": {"played_games": 0, 1: 0, 2: 0, 3: 0, 4: 0},
            },
            TenhouStatistics.DAN_LOBBY: {
                "all": {"played_games": 0, 1: 0, 2: 0, 3: 0, 4: 0},
                "current_month": {"played_games": 0, 1: 0, 2: 0, 3: 0, 4: 0},
            },
            TenhouStatistics.UPPERDAN_LOBBY: {
                "all": {"played_games": 0, 1: 0, 2: 0, 3: 0, 4: 0},
                "current_month": {"played_games": 0, 1: 0, 2: 0, 3: 0, 4: 0},
            },
            TenhouStatistics.PHOENIX_LOBBY: {
                "all": {"played_games": 0, 1: 0, 2: 0, 3: 0, 4: 0},
                "current_month": {"played_games": 0, 1: 0, 2: 0, 3: 0, 4: 0},
            },
        }

        for game in games:
            lobby_name = lobbies_dict[game.game_rules[1]]

            lobbies_data[lobby_name]["all"]["played_games"] += 1
            lobbies_data[lobby_name]["all"][game.place] += 1

            month_first_day = get_month_first_day()
            month_last_day = get_month_last_day()

            if month_first_day <= game.game_date <= month_last_day:
                lobbies_data[lobby_name]["current_month"]["played_games"] += 1
                lobbies_data[lobby_name]["current_month"][game.place] += 1

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
            stat_types = {"all": TenhouStatistics.ALL_TIME, "current_month": TenhouStatistics.CURRENT_MONTH}

            for key, stat_type in stat_types.items():
                if lobby_data[key]["played_games"]:
                    stat_object, _ = TenhouStatistics.objects.get_or_create(
                        lobby=lobby_key, tenhou_object=tenhou_object, stat_type=stat_type
                    )

                    games_count = lobby_data[key]["played_games"]
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
            total_average_place = (
                total_first_place + total_second_place * 2 + total_third_place * 3 + total_fourth_place * 4
            ) / total_played_games
        else:
            total_average_place = 0

        if month_played_games:
            month_average_place = (
                month_first_place + month_second_place * 2 + month_third_place * 3 + month_fourth_place * 4
            ) / month_played_games
        else:
            month_average_place = 0

        calculated_rank = FourPlayersPointsCalculator.calculate_rank(games)

        # some players are play sanma only
        # or in custom lobby only
        # we still need to keep for them last played date
        if all_games:
            last_played_date = all_games and all_games[-1]["game_date"] or None
        else:
            last_played_date = games.exists() and games.last().game_date or None

        tenhou_object.last_played_date = last_played_date
        tenhou_object.save()

        stat, _ = TenhouAggregatedStatistics.objects.get_or_create(
            game_players=TenhouAggregatedStatistics.FOUR_PLAYERS, tenhou_object=tenhou_object
        )

        rank = [x[0] for x in TenhouAggregatedStatistics.RANKS if x[1] == calculated_rank["rank"]][0]
        # 3 or less dan
        if rank <= 12:
            # we need to erase user rate when user lost 4 dan
            stat.rate = 0

        stat.rank = rank
        stat.pt = calculated_rank["pt"]
        stat.end_pt = calculated_rank["end_pt"]
        stat.last_played_date = last_played_date
        stat.played_games = total_played_games
        stat.average_place = total_average_place
        stat.month_played_games = month_played_games
        stat.month_average_place = month_average_place
        stat.save()


def download_all_games_from_arcturus(tenhou_username, username_created_at):
    url = "http://arcturus.su/tenhou/ranking/ranking.pl?name={}&d1={}".format(
        quote(tenhou_username, safe=""), username_created_at.strftime("%Y%m%d")
    )

    page = requests.get(url)
    soup = BeautifulSoup(page.content, "html.parser", from_encoding="utf-8")

    places_dict = {"1位": 1, "2位": 2, "3位": 3, "4位": 4}

    records = soup.find("div", {"id": "records"}).text.split("\n")
    player_games = []
    for record in records:
        if not record:
            continue

        temp_array = record.strip().split("|")
        game_rules = temp_array[5].strip()[:-1]

        place = places_dict[temp_array[0].strip()]
        lobby_number = temp_array[1].strip()

        # we don't have game length for custom lobby
        try:
            game_length = int(temp_array[2].strip())
        except ValueError:
            game_length = None

        date = temp_array[3].strip()
        time = temp_array[4].strip()
        date = datetime.strptime("{} {} +0900".format(date, time), "%Y-%m-%d %H:%M %z")

        player_games.append(
            {
                "place": place,
                "game_rules": game_rules,
                "game_length": game_length,
                "game_date": date,
                "lobby_number": lobby_number,
            }
        )

    return player_games


def save_played_games(tenhou_object, player_games):
    filtered_games = []
    for game in player_games:
        # let's collect stat only from usual games for 4 players
        if game["lobby_number"] == "L0000" and game["game_rules"][0] == "四":
            filtered_games.append(game)

    with transaction.atomic():
        for result in filtered_games:
            TenhouGameLog.objects.get_or_create(
                game_players=TenhouGameLog.FOUR_PLAYERS,
                tenhou_object=tenhou_object,
                place=result["place"],
                game_date=result["game_date"],
                game_rules=result["game_rules"],
                game_length=result["game_length"],
                lobby=lobbies_dict[result["game_rules"][1]],
            )


def get_started_date_for_account(tenhou_nickname):
    url = "http://arcturus.su/tenhou/ranking/ranking.pl?name={}".format(quote(tenhou_nickname, safe=""))

    page = requests.get(url)
    soup = BeautifulSoup(page.content, "html.parser", from_encoding="utf-8")

    previous_date = None
    account_start_date = None

    records = soup.find("div", {"id": "records"}).text.split("\n")
    for record in records:
        if not record:
            continue

        temp_array = record.strip().split("|")
        date = datetime.strptime(temp_array[3].strip(), "%Y-%m-%d")

        # let's initialize start date with first date in the list
        if not account_start_date:
            account_start_date = date

        if previous_date:
            delta = date - previous_date
            # it means that account wasn't used long time and was wiped
            if delta.days > 180:
                account_start_date = date

        previous_date = date

    return account_start_date
