# -*- coding: utf-8 -*-
import codecs
import struct
from urllib.parse import unquote
from urllib.request import urlopen

import re


class TenhouParser(object):

    def get_player_names(self, log_id):
        log_id = self._get_log_name_for_download(log_id)
        log_content = self._download_log(log_id).decode('utf-8')
        rounds = self._parse_rounds(log_content)

        players = []
        first_round = rounds[0]
        for tag in first_round:
            if tag.startswith('<UN'):
                players = [
                    unquote(self._get_attribute_content(tag, 'n0')),
                    unquote(self._get_attribute_content(tag, 'n1')),
                    unquote(self._get_attribute_content(tag, 'n2')),
                    unquote(self._get_attribute_content(tag, 'n3')),
                ]
                break

        return players

    def _download_log(self, log_id):
        resp = urlopen('http://e.mjv.jp/0/log/?' + log_id)
        data = resp.read()
        return data

    def _get_log_name_for_download(self, log_id):
        table = [
            22136, 52719, 55146, 42104,
            59591, 46934, 9248,  28891,
            49597, 52974, 62844, 4015,
            18311, 50730, 43056, 17939,
            64838, 38145, 27008, 39128,
            35652, 63407, 65535, 23473,
            35164, 55230, 27536, 4386,
            64920, 29075, 42617, 17294,
            18868, 2081
        ]

        code_pos = log_id.rindex("-") + 1
        code = log_id[code_pos:]
        if code[0] == 'x':
            a, b, c = struct.unpack(">HHH", bytes.fromhex(code[1:]))
            index = 0
            if log_id[:12] > "2010041111gm":
                x = int("3" + log_id[4:10])
                y = int(log_id[9])
                index = x % (33 - y)
            first = (a ^ b ^ table[index]) & 0xFFFF
            second = (b ^ c ^ table[index] ^ table[index + 1]) & 0xFFFF
            return log_id[:code_pos] + codecs.getencoder('hex_codec')(struct.pack(">HH", first, second))[0].decode('ASCII')
        else:
            return log_id

    def _parse_rounds(self, log_content):
        tag_start = 0
        rounds = []
        tag = None
        game_round = []
        for x in range(0, len(log_content)):
            if log_content[x] == '>':
                tag = log_content[tag_start:x+1]
                tag_start = x + 1

            # not useful tags
            if tag and ('mjloggm' in tag or 'TAIKYOKU' in tag or 'SHUFFLE seed=' in tag):
                tag = None

            # new round was started
            if tag and 'INIT' in tag:
                rounds.append(game_round)
                game_round = []

            # the end of the game
            if tag and 'owari' in tag:
                rounds.append(game_round)

            if tag:
                # to save some memory we can remove not needed information from logs
                if 'INIT' in tag:
                    # we dont need seed information
                    find = re.compile(r'shuffle="[^"]*"')
                    tag = find.sub('', tag)

                # add processed tag to the round
                game_round.append(tag)
                tag = None

        return rounds

    def _get_attribute_content(self, message, attribute_name):
        result = re.findall(r'{}="([^"]*)"'.format(attribute_name), message)
        return result and result[0] or None
