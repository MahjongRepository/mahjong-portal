# -*- coding: utf-8 -*-
from django.test import TestCase

from .views import update_placing


class TestUpdatePlacing(TestCase):
    def test_different_scores(self):
        rows = [
            [None, None, None, -100, None, 4],
            [None, None, None, 0, None, 4],
            [None, None, None, 100, None, 4],
        ]
        update_placing(rows)
        self.assertListEqual(
            [(row[0], row[3]) for row in rows], [(1, 100), (2, 0), (3, -100)],
        )

    def test_repeated_scores(self):
        rows = [
            [None, None, None, -100, None, 4],
            [None, None, None, 0, None, 4],
            [None, None, None, 100, None, 4],
            [None, None, None, 0, None, 4],
            [None, None, None, -200, None, 4],
            [None, None, None, 0, None, 4],
            [None, None, None, -100, None, 4],
        ]
        update_placing(rows)
        self.assertListEqual(
            [(row[0], row[3]) for row in rows], [(1, 100), (2, 0), (2, 0), (2, 0), (5, -100), (5, -100), (7, -200)],
        )

    def test_different_game_counts(self):
        rows = [
            [None, None, None, 100, None, 2],
            [None, None, None, -100, None, 3],
            [None, None, None, -100, None, 4],
            [None, None, None, 0, None, 4],
        ]
        update_placing(rows)
        self.assertListEqual(
            [(row[0], row[3]) for row in rows], [(1, 0), (2, -100), (3, -100), (4, 100)],
        )
