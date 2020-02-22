# -*- coding: utf-8 -*-
from copy import copy
from datetime import datetime

import pytz


class FourPlayersPointsCalculator:
    """
    Calculate how much points user will get from games in various lobby's
    """

    LOBBY = {
        "般_old": {"東": {1: 30}, "南": {1: 45}},
        "般": {"東": {1: 20, 2: 10}, "南": {1: 30, 2: 15}},
        "上": {"東": {1: 40, 2: 10}, "南": {1: 60, 2: 15}},
        "特": {"東": {1: 50, 2: 20}, "南": {1: 75, 2: 30}},
        "鳳": {"東": {1: 60, 2: 30}, "南": {1: 90, 2: 45}},
    }

    DAN_SETTINGS = {
        "新人": {"rank": "新人", "start_pt": 0, "end_pt": 20, "東": 0, "南": 0},
        "９級": {"rank": "９級", "start_pt": 0, "end_pt": 20, "東": 0, "南": 0},
        "８級": {"rank": "８級", "start_pt": 0, "end_pt": 20, "東": 0, "南": 0},
        "７級": {"rank": "７級", "start_pt": 0, "end_pt": 20, "東": 0, "南": 0},
        "６級": {"rank": "６級", "start_pt": 0, "end_pt": 40, "東": 0, "南": 0},
        "５級": {"rank": "５級", "start_pt": 0, "end_pt": 60, "東": 0, "南": 0},
        "４級": {"rank": "４級", "start_pt": 0, "end_pt": 80, "東": 0, "南": 0},
        "３級": {"rank": "３級", "start_pt": 0, "end_pt": 100, "東": 0, "南": 0},
        "２級": {"rank": "２級", "start_pt": 0, "end_pt": 100, "東": 10, "南": 15},
        "１級": {"rank": "１級", "start_pt": 0, "end_pt": 100, "東": 20, "南": 30},
        "初段": {"rank": "初段", "start_pt": 200, "end_pt": 400, "東": 30, "南": 45},
        "二段": {"rank": "二段", "start_pt": 400, "end_pt": 800, "東": 40, "南": 60},
        "三段": {"rank": "三段", "start_pt": 600, "end_pt": 1200, "東": 50, "南": 75},
        "四段": {"rank": "四段", "start_pt": 800, "end_pt": 1600, "東": 60, "南": 90},
        "五段": {"rank": "五段", "start_pt": 1000, "end_pt": 2000, "東": 70, "南": 105},
        "六段": {"rank": "六段", "start_pt": 1200, "end_pt": 2400, "東": 80, "南": 120},
        "七段": {"rank": "七段", "start_pt": 1400, "end_pt": 2800, "東": 90, "南": 135},
        "八段": {"rank": "八段", "start_pt": 1600, "end_pt": 3200, "東": 100, "南": 150},
        "九段": {"rank": "九段", "start_pt": 1800, "end_pt": 3600, "東": 110, "南": 165},
        "十段": {"rank": "十段", "start_pt": 2000, "end_pt": 4000, "東": 120, "南": 180},
    }

    OLD_RANK_LIMITS = {"新人": 30, "９級": 30, "８級": 30, "７級": 60, "６級": 60, "５級": 60, "４級": 90}

    @staticmethod
    def calculate_rank(games):
        rank = copy(FourPlayersPointsCalculator.DAN_SETTINGS["新人"])
        rank["pt"] = rank["start_pt"]

        kyu_lobby_changes_date = datetime(2017, 10, 24, 0, 0, tzinfo=pytz.utc)

        lobbies = ["般", "上", "特", "鳳"]
        for game in games:
            lobby = lobbies[game.lobby]

            # we have different values for old games
            if game.game_date < kyu_lobby_changes_date:
                # lobby + pt was different
                if lobby == "般":
                    lobby = "般_old"

                if FourPlayersPointsCalculator.OLD_RANK_LIMITS.get(rank["rank"]):
                    rank["end_pt"] = FourPlayersPointsCalculator.OLD_RANK_LIMITS.get(rank["rank"])

            delta = 0
            if game.place == 1 or game.place == 2:
                delta = FourPlayersPointsCalculator.LOBBY[lobby][game.game_type].get(game.place, 0)
            elif game.place == 4:
                delta = -FourPlayersPointsCalculator.DAN_SETTINGS[rank["rank"]][game.game_type]

            rank_index = list(FourPlayersPointsCalculator.DAN_SETTINGS.keys()).index(rank["rank"])

            rank["pt"] += delta
            game.delta = delta
            game.rank = rank_index
            game.next_rank = rank_index

            # new dan
            if rank["pt"] >= rank["end_pt"]:
                # getting next record from ordered dict
                next_rank = list(FourPlayersPointsCalculator.DAN_SETTINGS.keys())[rank_index + 1]
                game.next_rank = rank_index + 1

                rank = copy(FourPlayersPointsCalculator.DAN_SETTINGS[next_rank])
                rank["pt"] = rank["start_pt"]
            # wasted dan
            elif rank["pt"] < 0:
                if rank["start_pt"] > 0:
                    # getting previous record from ordered dict
                    next_rank = list(FourPlayersPointsCalculator.DAN_SETTINGS.keys())[rank_index - 1]
                    game.next_rank = rank_index - 1
                    rank = copy(FourPlayersPointsCalculator.DAN_SETTINGS[next_rank])
                    rank["pt"] = rank["start_pt"]
                else:
                    # we can't lose first kyu
                    rank["pt"] = 0

            game.save()

        return rank
