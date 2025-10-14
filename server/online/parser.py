# -*- coding: utf-8 -*-
import codecs
import math
import re
import struct
from urllib.parse import unquote

import requests


class TenhouParser(object):
    def get_ratings(self, log_id):
        log_id = self._get_log_name_for_download(log_id)
        log_content = self._download_log(log_id)
        rounds = self._parse_rounds(log_content)

        players_map_with_rates = []
        first_round = rounds[0]
        last_round = rounds[len(rounds) - 1]
        for tag in first_round:
            if tag.startswith("<UN"):
                current_rates = unquote(self._get_attribute_content(tag, "rate")).strip().split(",")
                players_map_with_rates = {
                    1: {
                        "rate": math.floor(float(current_rates[0])),
                        "nickname": unquote(self._get_attribute_content(tag, "n0")),
                    },
                    2: {
                        "rate": math.floor(float(current_rates[1])),
                        "nickname": unquote(self._get_attribute_content(tag, "n1")),
                    },
                    3: {
                        "rate": math.floor(float(current_rates[2])),
                        "nickname": unquote(self._get_attribute_content(tag, "n2")),
                    },
                    4: {
                        "rate": math.floor(float(current_rates[3])),
                        "nickname": unquote(self._get_attribute_content(tag, "n3")),
                    },
                }
                break

        for tag in last_round:
            if tag.startswith("<AGARI") or tag.startswith("<RYUUKYOKU"):
                current_parsed_results = unquote(self._get_attribute_content(tag, "owari")).strip().split(",")
                current_results = {
                    1: current_parsed_results[1],
                    2: current_parsed_results[3],
                    3: current_parsed_results[5],
                    4: current_parsed_results[7],
                }
                sorted_results = dict(sorted(current_results.items(), key=lambda item: float(item[1]), reverse=True))

                current_place = 1
                for player_index, _ in sorted_results.items():
                    players_map_with_rates[player_index]["place"] = current_place
                    current_place += 1

                break

        return players_map_with_rates

    def get_player_names(self, log_id):
        log_id = self._get_log_name_for_download(log_id)
        log_content = self._download_log(log_id)
        rounds = self._parse_rounds(log_content)

        players = []
        first_round = rounds[0]
        for tag in first_round:
            if tag.startswith("<UN"):
                players = [
                    unquote(self._get_attribute_content(tag, "n0")),
                    unquote(self._get_attribute_content(tag, "n1")),
                    unquote(self._get_attribute_content(tag, "n2")),
                    unquote(self._get_attribute_content(tag, "n3")),
                ]
                break

        return players

    def _download_log(self, log_id):
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0"}
        response = requests.get("https://tenhou.net/0/log/?{}".format(log_id), headers=headers)
        data = response.text
        return data

    def _get_log_name_for_download(self, log_id):
        table = [
            22136,
            52719,
            55146,
            42104,
            59591,
            46934,
            9248,
            28891,
            49597,
            52974,
            62844,
            4015,
            18311,
            50730,
            43056,
            17939,
            64838,
            38145,
            27008,
            39128,
            35652,
            63407,
            65535,
            23473,
            35164,
            55230,
            27536,
            4386,
            64920,
            29075,
            42617,
            17294,
            18868,
            2081,
        ]

        code_pos = log_id.rindex("-") + 1
        code = log_id[code_pos:]
        if code[0] == "x":
            a, b, c = struct.unpack(">HHH", bytes.fromhex(code[1:]))
            index = 0
            if log_id[:12] > "2010041111gm":
                x = int("3" + log_id[4:10])
                y = int(log_id[9])
                index = x % (33 - y)
            first = (a ^ b ^ table[index]) & 0xFFFF
            second = (b ^ c ^ table[index] ^ table[index + 1]) & 0xFFFF
            result = codecs.getencoder("hex_codec")(struct.pack(">HH", first, second))[0].decode("ASCII")
            return log_id[:code_pos] + result
        else:
            return log_id

    def _parse_rounds(self, log_content):
        tag_start = 0
        rounds = []
        tag = None
        game_round = []
        for x in range(0, len(log_content)):
            if log_content[x] == ">":
                tag = log_content[tag_start : x + 1]
                tag_start = x + 1

            # not useful tags
            if tag and ("mjloggm" in tag or "TAIKYOKU" in tag or "SHUFFLE seed=" in tag):
                tag = None

            # new round was started
            if tag and "INIT" in tag:
                rounds.append(game_round)
                game_round = []

            # the end of the game
            if tag and "owari" in tag:
                rounds.append(game_round)

            if tag:
                # to save some memory we can remove not needed information from logs
                if "INIT" in tag:
                    # we dont need seed information
                    find = re.compile(r'shuffle="[^"]*"')
                    tag = find.sub("", tag)

                # add processed tag to the round
                game_round.append(tag)
                tag = None

        return rounds

    def _get_attribute_content(self, message, attribute_name):
        result = re.findall(r'{}="([^"]*)"'.format(attribute_name), message)
        return result and result[0] or None
