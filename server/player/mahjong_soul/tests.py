from datetime import datetime

import pytz
from django.test import TestCase

from player.mahjong_soul.models import MSAccount, MSAccountStatistic, MSPointsHistory
from player.models import Player


class MahjongSoulViewTestCase(TestCase):
    ms_account: MSAccount
    stat_object: MSAccountStatistic

    def setUp(self):
        player = Player.objects.create()
        self.ms_account = MSAccount.objects.create(player=player, account_name="test", account_id=101)
        self.stat_object = MSAccountStatistic.objects.create(
            account=self.ms_account, game_type=MSAccountStatistic.FOUR_PLAYERS,
        )

    def test_get_points_history_for_latest_rank_expect_only_latest_rank(self):
        self.create_points_history(
            [
                {"date": datetime(2020, 10, 4, 0, 0, 0, tzinfo=pytz.utc), "rank": 1, "points": 100},
                {"date": datetime(2020, 10, 4, 0, 15, 0, tzinfo=pytz.utc), "rank": 0, "points": 100},
                {"date": datetime(2020, 10, 4, 0, 30, 0, tzinfo=pytz.utc), "rank": 0, "points": 100},
                {"date": datetime(2020, 10, 4, 0, 45, 0, tzinfo=pytz.utc), "rank": 1, "points": 100},
                {"date": datetime(2020, 10, 4, 1, 0, 0, tzinfo=pytz.utc), "rank": 1, "points": 100},
            ],
        )
        history = self.stat_object.get_points_history_for_latest_rank()
        self.assertEqual(history.count(), 2)
        self.assertEqual(
            history.last().created_on, datetime(2020, 10, 4, 1, 0, 0, tzinfo=pytz.utc),
        )

    def create_points_history(self, records):
        history = []
        rank_index = 0
        for record in records:
            if history and history[-1].rank != record["rank"]:
                rank_index += 1
            history.append(
                MSPointsHistory.objects.create(
                    stat_object=self.stat_object, points=record["points"], rank=record["rank"], rank_index=rank_index,
                ),
            )
            history[-1].created_on = record["date"]
            history[-1].save()
        return history
