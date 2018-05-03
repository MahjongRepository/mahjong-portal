from datetime import datetime

from django.test import TestCase

from utils.tenhou.points_calculator import PointsCalculator


class TenhouCalculatorTestCase(TestCase):

    def test_calculations(self):
        game_records = self._generate_game_records([1, 1, 2, 3, 1, 1, 4, 2])
        result = PointsCalculator.calculate_rank(game_records)
        self.assertEqual(result['rank'], u'６級')
        self.assertEqual(result['pt'], 15)

    def test_hanchan_and_tonpusen(self):
        game_records = [
            {'date': datetime.now().date(), 'lobby': u'般', 'place': 1, 'game_type': u'東'},
            {'date': datetime.now().date(), 'lobby': u'般', 'place': 1, 'game_type': u'南'},
            {'date': datetime.now().date(), 'lobby': u'般', 'place': 1, 'game_type': u'東'},
            {'date': datetime.now().date(), 'lobby': u'般', 'place': 1, 'game_type': u'東'},
            {'date': datetime.now().date(), 'lobby': u'般', 'place': 1, 'game_type': u'東'},
        ]

        result = PointsCalculator.calculate_rank(game_records)
        self.assertEqual(result['rank'], u'６級')
        self.assertEqual(result['pt'], 20)

    def test_old_and_new_kyu_lobby_append_points(self):
        game_records = [
            {'date': datetime(2017, 10, 23).date(), 'lobby': u'般', 'place': 2, 'game_type': u'南'},
            {'date': datetime.now().date(), 'lobby': u'般', 'place': 2, 'game_type': u'南'},
        ]

        result = PointsCalculator.calculate_rank(game_records)
        self.assertEqual(result['rank'], u'新人')
        self.assertEqual(result['pt'], 15)

    def test_old_kyu_lobby_rank_limits(self):
        game_records = [
            {'date': datetime(2017, 10, 23).date(), 'lobby': u'般', 'place': 1, 'game_type': u'南'},
            {'date': datetime(2017, 10, 23).date(), 'lobby': u'般', 'place': 1, 'game_type': u'南'},
            {'date': datetime(2017, 10, 23).date(), 'lobby': u'般', 'place': 1, 'game_type': u'南'},
            {'date': datetime(2017, 10, 23).date(), 'lobby': u'般', 'place': 1, 'game_type': u'南'},
        ]

        result = PointsCalculator.calculate_rank(game_records)
        self.assertEqual(result['rank'], u'７級')
        self.assertEqual(result['pt'], 45)

    def test_you_cant_lose_1_kyu(self):
        first_places = [1] * 19
        game_records = self._generate_game_records(first_places + [4])
        result = PointsCalculator.calculate_rank(game_records)
        self.assertEqual(result['rank'], u'１級')
        self.assertEqual(result['pt'], 0)

    def _generate_game_records(self, places, lobby=u'般', game_type=u'南'):
        data = []
        for place in places:
            data.append({'date': datetime.now().date(), 'lobby': lobby, 'place': place, 'game_type': game_type})
        return data
