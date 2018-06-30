from datetime import datetime, timedelta

import pytz
from django.test import TestCase
from django.utils import timezone

from player.models import Player
from player.tenhou.models import TenhouNickname, TenhouGameLog, TenhouStatistics
from utils.tenhou.points_calculator import PointsCalculator


class TenhouCalculatorTestCase(TestCase):

    def setUp(self):
        player = Player.objects.create()
        self.tenhou_object = TenhouNickname.objects.create(
            player=player,
            tenhou_username='test',
            username_created_at=timezone.now(),
            rank=0
        )

    def test_calculations(self):
        game_records = self._create_game_record(self._generate_game_records([1, 1, 2, 3, 1, 1, 4, 2]))
        result = PointsCalculator.calculate_rank(game_records)
        self.assertEqual(result['rank'], u'６級')
        self.assertEqual(result['pt'], 15)

    def test_hanchan_and_tonpusen(self):
        game_records = self._create_game_record([
            {'date': timezone.now() + timedelta(seconds=0), 'game_rules': u'四般東', 'place': 1},
            {'date': timezone.now() + timedelta(seconds=1), 'game_rules': u'四般南', 'place': 1},
            {'date': timezone.now() + timedelta(seconds=2), 'game_rules': u'四般東', 'place': 1},
            {'date': timezone.now() + timedelta(seconds=3), 'game_rules': u'四般東', 'place': 1},
            {'date': timezone.now() + timedelta(seconds=4), 'game_rules': u'四般東', 'place': 1},
        ])

        result = PointsCalculator.calculate_rank(game_records)
        self.assertEqual(result['rank'], u'６級')
        self.assertEqual(result['pt'], 20)

    def test_old_and_new_kyu_lobby_append_points(self):
        game_records = self._create_game_record([
            {'date': datetime(2017, 10, 23, tzinfo=pytz.utc), 'game_rules': u'四般南', 'place': 2},
            {'date': timezone.now(), 'game_rules': u'四般南', 'place': 2},
        ])

        result = PointsCalculator.calculate_rank(game_records)
        self.assertEqual(result['rank'], u'新人')
        self.assertEqual(result['pt'], 15)

    def test_old_kyu_lobby_rank_limits(self):
        game_records = self._create_game_record([
            {'date': datetime(2017, 10, 23, tzinfo=pytz.utc) + timedelta(seconds=0), 'game_rules': u'四般南', 'place': 1},
            {'date': datetime(2017, 10, 23, tzinfo=pytz.utc) + timedelta(seconds=2), 'game_rules': u'四般南', 'place': 1},
            {'date': datetime(2017, 10, 23, tzinfo=pytz.utc) + timedelta(seconds=3), 'game_rules': u'四般南', 'place': 1},
            {'date': datetime(2017, 10, 23, tzinfo=pytz.utc) + timedelta(seconds=4), 'game_rules': u'四般南', 'place': 1},
        ])

        result = PointsCalculator.calculate_rank(game_records)
        self.assertEqual(result['rank'], u'７級')
        self.assertEqual(result['pt'], 45)

    def test_you_cant_lose_1_kyu(self):
        first_places = [1] * 19
        game_records = self._create_game_record(self._generate_game_records(first_places + [4]))
        result = PointsCalculator.calculate_rank(game_records)
        self.assertEqual(result['rank'], u'１級')
        self.assertEqual(result['pt'], 0)

    def _generate_game_records(self, places):
        data = []
        for place in places:
            data.append({'date': timezone.now(), 'place': place, 'game_rules': u'四般南'})
        return data

    def _create_game_record(self, game_records):
        records = []
        for game_record in game_records:
            records.append(
                TenhouGameLog.objects.create(
                    tenhou_object=self.tenhou_object,
                    game_date=game_record['date'],
                    place=game_record['place'],
                    game_rules=game_record['game_rules'],
                    lobby=TenhouStatistics.KYU_LOBBY,
                    game_length=10
                )
            )
        return records
