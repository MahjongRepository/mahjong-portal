# -*- coding: utf-8 -*-
from datetime import datetime
from urllib.parse import quote, unquote

import pytz
import requests
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


def recalculate_tenhou_statistics_for_four_players(tenhou_object, all_games=None, four_players_rate=None):
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

        if four_players_rate:
            stat.rate = four_players_rate

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


def download_all_games_from_nodochi(tenhou_username):
    url = f"https://nodocchi.moe/api/listuser.php?name={quote(tenhou_username)}"
    response = requests.get(url).json()

    lobbies_dict = {
        "0": TenhouStatistics.KYU_LOBBY,
        "1": TenhouStatistics.DAN_LOBBY,
        "2": TenhouStatistics.UPPERDAN_LOBBY,
        "3": TenhouStatistics.PHOENIX_LOBBY,
    }

    lobbies_tenhou_dict = {
        "0": "般",
        "1": "上",
        "2": "特",
        "3": "鳳",
    }

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

    if response.get("rate"):
        four_games_rate = response.get("rate").get("4", None)
    else:
        four_games_rate = None

    account_start_date = datetime.utcfromtimestamp(int(response["rseq"][-1][0])).replace(
        tzinfo=pytz.timezone("Asia/Tokyo")
    )

    games = response.get("list", [])

    month_first_day = get_month_first_day().date()
    month_last_day = get_month_last_day().date()

    player_games = []
    for game in games:
        # usual and phoenix games
        if game["sctype"] == "b" or game["sctype"] == "c":
            # api doesnt' return player place we had to assume from game results
            place = None
            for x in range(1, 5):
                if game["player{}".format(x)] == tenhou_username:
                    place = x
                    break

            if game["playlength"] == "1":
                game_type = "東"
            else:
                game_type = "南"

            game_date = datetime.utcfromtimestamp(int(game["starttime"])).replace(tzinfo=pytz.timezone("Asia/Tokyo"))

            lobby_name = lobbies_dict[game["playerlevel"]]
            lobbies_data[lobby_name]["all"]["played_games"] += 1
            lobbies_data[lobby_name]["all"][place] += 1

            if month_first_day <= game_date.date() <= month_last_day:
                lobbies_data[lobby_name]["current_month"]["played_games"] += 1
                lobbies_data[lobby_name]["current_month"][place] += 1

            # emulate game_rules string from arcturus
            game_rules = ""
            if int(game["playernum"]) == 4:
                game_rules = "四"
            else:
                game_rules = "二"
            game_rules += lobbies_tenhou_dict[game["playerlevel"]]
            game_rules += game_type

            player_games.append(
                {
                    "game_date": game_date,
                    "place": place,
                    "lobby": lobbies_tenhou_dict[game["playerlevel"]],
                    "game_type": game_type,
                    "lobby_number": game.get("lobby") or "L0000",
                    "game_rules": game_rules,
                    "game_length": int(game.get("during") or 0),
                }
            )

    return player_games, account_start_date, four_games_rate


def save_played_games(tenhou_object, player_games):
    filtered_games = []
    for game in player_games:
        if game["game_date"] < tenhou_object.username_created_at:
            continue

        # let's collect stat only from usual games for 4 players
        if game["lobby_number"] == "L0000" and game["game_rules"][0] == "四":
            filtered_games.append(game)

    with transaction.atomic():
        for result in filtered_games:
            try:
                TenhouGameLog.objects.get(
                    game_players=TenhouGameLog.FOUR_PLAYERS,
                    tenhou_object=tenhou_object,
                    place=result["place"],
                    game_date=result["game_date"],
                    lobby=lobbies_dict[result["game_rules"][1]],
                )
            # after moving to nodochi game_rules changed, so we can't use get_or_create anymore
            except TenhouGameLog.DoesNotExist:
                TenhouGameLog.objects.create(
                    game_players=TenhouGameLog.FOUR_PLAYERS,
                    tenhou_object=tenhou_object,
                    place=result["place"],
                    game_date=result["game_date"],
                    game_rules=result["game_rules"],
                    game_length=result["game_length"],
                    lobby=lobbies_dict[result["game_rules"][1]],
                )


def parse_names_from_tenhou_chat_message(message: str):
    tmp = message.split(" ")[1:-1]
    results = []
    for item in tmp:
        name = item.split("(")[0]
        results.append(unquote(name))
    return results
