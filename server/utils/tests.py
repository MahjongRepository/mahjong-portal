# -*- coding: utf-8 -*-
from django.test import TestCase

from utils.tenhou.helper import parse_log_line


class ParseLogLinesTestCase(TestCase):
    def test_parse_line(self):
        line = "22:34 | 23 | 四上南喰赤－ | 天草(+48.0) 宮永|咲(+2.0) Curtis(-19.0) 橋から(-31.0)"

        results = parse_log_line(line)
        self.assertEqual(results["players"][0]["name"], "天草")
        self.assertEqual(results["players"][0]["place"], 1)
        self.assertEqual(results["players"][1]["name"], "宮永|咲")
        self.assertEqual(results["players"][1]["place"], 2)
        self.assertEqual(results["players"][2]["name"], "Curtis")
        self.assertEqual(results["players"][2]["place"], 3)
        self.assertEqual(results["players"][3]["name"], "橋から")
        self.assertEqual(results["players"][3]["place"], 4)

        self.assertEqual(results["game_rules"], "四上南喰赤－")

    def test_parse_line_with_brace_symbol_in_name(self):
        line = "23:56 | 11 | 三般東喰赤－ | 烏龍茶(黒)(+43.0) misery20(-7.0) NoName(-36.0)"

        results = parse_log_line(line)
        self.assertEqual(results["players"][0]["name"], "烏龍茶(黒)")
        self.assertEqual(results["players"][1]["name"], "misery20")
        self.assertEqual(results["players"][2]["name"], "NoName")
