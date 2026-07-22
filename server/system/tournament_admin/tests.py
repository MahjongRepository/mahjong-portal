# -*- coding: utf-8 -*-
from django.test import TestCase

from .views import FilteredResult, update_placing


class TestUpdatePlacing(TestCase):
    def test_different_scores(self):
        rows = [
            FilteredResult(scores=-100, games=4),
            FilteredResult(scores=0, games=4),
            FilteredResult(scores=100, games=4),
        ]
        update_placing(rows)
        self.assertListEqual(
            [(row.place, row.scores) for row in rows],
            [(1, 100), (2, 0), (3, -100)],
        )

    def test_repeated_scores(self):
        rows = [
            FilteredResult(scores=-100, games=4),
            FilteredResult(scores=0, games=4),
            FilteredResult(scores=100, games=4),
            FilteredResult(scores=0, games=4),
            FilteredResult(scores=-200, games=4),
            FilteredResult(scores=0, games=4),
            FilteredResult(scores=-100, games=4),
        ]
        update_placing(rows)
        self.assertListEqual(
            [(row.place, row.scores) for row in rows],
            [(1, 100), (2, 0), (2, 0), (2, 0), (5, -100), (5, -100), (7, -200)],
        )

    def test_different_game_counts(self):
        rows = [
            FilteredResult(scores=100, games=2),
            FilteredResult(scores=-100, games=3),
            FilteredResult(scores=-100, games=4),
            FilteredResult(scores=0, games=4),
        ]
        update_placing(rows)
        self.assertListEqual(
            [(row.place, row.scores) for row in rows],
            [(1, 0), (2, -100), (3, -100), (4, 100)],
        )
