import json
import re
from base64 import b64decode
from collections import OrderedDict
from copy import copy
from datetime import datetime

import pytz
import requests
from django.conf import settings


class TenhouCalculator(object):
    LOBBY = {
        '般_old': {
            '東': {1: 30},
            '南': {1: 45},
        },
        '般': {
            '東': {1: 20, 2: 10},
            '南': {1: 30, 2: 15},
        },
        '上': {
            '東': {1: 40, 2: 10},
            '南': {1: 60, 2: 15},
        },
        '特': {
            '東': {1: 50, 2: 20},
            '南': {1: 75, 2: 30},
        },
        '鳳': {
            '東': {1: 60, 2: 30},
            '南': {1: 90, 2: 45},
        }
    }

    DAN_SETTINGS = OrderedDict({
        '新人': {
            'rank': '新人',
            'start_pt': 0,
            'end_pt': 20,
            '東': 0,
            '南': 0,
        },
        '９級': {
            'rank': '９級',
            'start_pt': 0,
            'end_pt': 20,
            '東': 0,
            '南': 0,
        },
        '８級': {
            'rank': '８級',
            'start_pt': 0,
            'end_pt': 20,
            '東': 0,
            '南': 0,
        },
        '７級': {
            'rank': '７級',
            'start_pt': 0,
            'end_pt': 20,
            '東': 0,
            '南': 0,
        },
        '６級': {
            'rank': '６級',
            'start_pt': 0,
            'end_pt': 40,
            '東': 0,
            '南': 0,
        },
        '５級': {
            'rank': '５級',
            'start_pt': 0,
            'end_pt': 60,
            '東': 0,
            '南': 0,
        },
        '４級': {
            'rank': '４級',
            'start_pt': 0,
            'end_pt': 80,
            '東': 0,
            '南': 0,
        },
        '３級': {
            'rank': '３級',
            'start_pt': 0,
            'end_pt': 100,
            '東': 0,
            '南': 0,
        },
        '２級': {
            'rank': '２級',
            'start_pt': 0,
            'end_pt': 100,
            '東': 10,
            '南': 15,
        },
        '１級': {
            'rank': '１級',
            'start_pt': 0,
            'end_pt': 100,
            '東': 20,
            '南': 30,
        },
        '初段': {
            'rank': '初段',
            'start_pt': 200,
            'end_pt': 400,
            '東': 30,
            '南': 45,
        },
        '二段': {
            'rank': '二段',
            'start_pt': 400,
            'end_pt': 800,
            '東': 40,
            '南': 60,
        },
        '三段': {
            'rank': '三段',
            'start_pt': 600,
            'end_pt': 1200,
            '東': 50,
            '南': 75,
        },
        '四段': {
            'rank': '四段',
            'start_pt': 800,
            'end_pt': 1600,
            '東': 60,
            '南': 90,
        },
        '五段': {
            'rank': '五段',
            'start_pt': 1000,
            'end_pt': 2000,
            '東': 70,
            '南': 105,
        },
        '六段': {
            'rank': '六段',
            'start_pt': 1200,
            'end_pt': 2400,
            '東': 80,
            '南': 120,
        },
        '七段': {
            'rank': '七段',
            'start_pt': 1400,
            'end_pt': 2800,
            '東': 90,
            '南': 135,
        },
        '八段': {
            'rank': '八段',
            'start_pt': 1600,
            'end_pt': 3200,
            '東': 100,
            '南': 150,
        },
        '九段': {
            'rank': '九段',
            'start_pt': 1800,
            'end_pt': 3600,
            '東': 110,
            '南': 165,
        },
        '十段': {
            'rank': '十段',
            'start_pt': 2000,
            'end_pt': 4000,
            '東': 120,
            '南': 180,
        }
    })

    OLD_RANK_LIMITS = {
        '新人': 30,
        '９級': 30,
        '８級': 30,
        '７級': 60,
        '６級': 60,
        '５級': 60,
        '４級': 90,
    }

    @staticmethod
    def calculate_rank(game_records):
        rank = copy(TenhouCalculator.DAN_SETTINGS['新人'])
        rank['pt'] = rank['start_pt']

        kyu_lobby_changes_date = datetime(2017, 10, 24).date()

        for game_record in game_records:
            date = game_record['date']
            place = game_record['place']
            lobby = game_record['lobby']
            game_type = game_record['game_type']

            # we have different values for old games
            if date < kyu_lobby_changes_date:
                # lobby + pt was different
                if lobby == '般':
                    lobby = '般_old'

                if TenhouCalculator.OLD_RANK_LIMITS.get(rank['rank']):
                    rank['end_pt'] = TenhouCalculator.OLD_RANK_LIMITS.get(rank['rank'])

            if place == 1 or place == 2:
                rank['pt'] += TenhouCalculator.LOBBY[lobby][game_type].get(place, 0)
            elif place == 4:
                rank['pt'] -= TenhouCalculator.DAN_SETTINGS[rank['rank']][game_type]

            # new dan
            if rank['pt'] >= rank['end_pt']:
                # getting next record from ordered dict
                rank_index = list(TenhouCalculator.DAN_SETTINGS.keys()).index(rank['rank'])
                next_rank = list(TenhouCalculator.DAN_SETTINGS.keys())[rank_index + 1]

                rank = copy(TenhouCalculator.DAN_SETTINGS[next_rank])
                rank['pt'] = rank['start_pt']
            # wasted dan
            elif rank['pt'] < 0:
                # getting previous record from ordered dict
                rank_index = list(TenhouCalculator.DAN_SETTINGS.keys()).index(rank['rank'])
                next_rank = list(TenhouCalculator.DAN_SETTINGS.keys())[rank_index - 1]

                if TenhouCalculator.DAN_SETTINGS[next_rank]['start_pt'] > 0:
                    rank = copy(TenhouCalculator.DAN_SETTINGS[next_rank])
                    rank['pt'] = rank['start_pt']
                else:
                    # we can't lose first kyu
                    rank['pt'] = 0
        return rank


def get_latest_wg_games():
    text = requests.get(settings.TENHOU_WG_URL).text
    text = text.replace('\r\n', '')
    data = json.loads(re.match('sw\((.*)\);', text).group(1))
    active_games = []
    for game in data:
        game_id, _, start_time, game_type, *players_data = game.split(',')
        players = []
        i = 0
        for name, dan, rate in [players_data[i:i+3] for i in range(0, len(players_data), 3)]:
            players.append({
                'name': b64decode(name).decode('utf-8'),
                'dan': int(dan),
                'rate': float(rate),
                'game_link': 'http://tenhou.net/0/?wg={}&tw={}'.format(game_id, i)
            })
            i += 1

        current_date = datetime.now(tz=pytz.timezone('Asia/Tokyo'))
        # Asia/Tokyo tz didn't work here (it added additional 30 minutes)
        # so I just added 9 hours
        start_time = '{} {} +0900'.format(current_date.strftime('%Y-%d-%m'), start_time)
        start_time = datetime.strptime(start_time, '%Y-%d-%m %H:%M %z')

        game = {
            'start_time': start_time,
            'game_id': game_id,
            'game_type': game_type,
            'players': players,
        }

        active_games.append(game)
    return reversed(active_games)
