# -*- coding: utf-8 -*-
import json
import re
from base64 import b64decode
from datetime import datetime, timedelta

import requests
from django.conf import settings


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

        current_date = datetime.now()

        hour = start_time[0:2]
        if hour[0] == '0' and int(hour[1]) < 9:
            current_date += timedelta(days=1)

        # Asia/Tokyo tz didn't work here (it added additional 30 minutes)
        # so I just added 9 hours
        start_time = '{} {} +0900'.format(current_date.strftime('%Y-%d-%m'), start_time)
        start_time = datetime.strptime(start_time, '%Y-%d-%m %H:%M %z')

        # need to find better way to do it
        rules = bin(int(game_type)).replace('0b', '')
        while len(rules) != 8:
            rules = '0' + rules

        is_hanchan = rules[4] == '1'

        game = {
            'start_time': start_time,
            'game_id': game_id,
            'game_type': is_hanchan and u'東' or u'南',
            'players': players,
        }

        active_games.append(game)

    return reversed(active_games)
