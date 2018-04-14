from datetime import datetime

from django.test import TestCase

from settings.utils import TenhouCalculator


class TenhouCalculatorTestCase(TestCase):

    def test_calculations(self):
        game_records = self._generate_game_records([1, 1, 2, 3, 1, 1, 4, 2])
        result = TenhouCalculator.calculate_rank(game_records)
        self.assertEqual(result['rank'], u'６級')
        self.assertEqual(result['pt'], 15)

    def test_hanchan_and_tonpusen(self):
        game_records = [
            {'date': datetime.now(), 'lobby': u'般', 'place': 1, 'game_type': u'東'},
            {'date': datetime.now(), 'lobby': u'般', 'place': 1, 'game_type': u'南'},
            {'date': datetime.now(), 'lobby': u'般', 'place': 1, 'game_type': u'東'},
            {'date': datetime.now(), 'lobby': u'般', 'place': 1, 'game_type': u'東'},
            {'date': datetime.now(), 'lobby': u'般', 'place': 1, 'game_type': u'東'},
        ]

        result = TenhouCalculator.calculate_rank(game_records)
        self.assertEqual(result['rank'], u'６級')
        self.assertEqual(result['pt'], 20)

    def test_old_and_new_kyu_lobby(self):
        game_records = [
            {'date': datetime(2017, 10, 23), 'lobby': u'般', 'place': 2, 'game_type': u'南'},
            {'date': datetime.now(), 'lobby': u'般', 'place': 2, 'game_type': u'南'},
        ]

        result = TenhouCalculator.calculate_rank(game_records)
        self.assertEqual(result['rank'], u'新人')
        self.assertEqual(result['pt'], 15)

    def test_you_cant_lose_1_kyu(self):
        first_places = [1] * 19
        game_records = self._generate_game_records(first_places + [4])
        result = TenhouCalculator.calculate_rank(game_records)
        self.assertEqual(result['rank'], u'１級')
        self.assertEqual(result['pt'], 0)

    def _generate_game_records(self, places, lobby=u'般', game_type=u'南'):
        data = []
        for place in places:
            data.append({'date': datetime.now(), 'lobby': lobby, 'place': place, 'game_type': game_type})
        return data
