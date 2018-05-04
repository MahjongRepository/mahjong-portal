from datetime import datetime
from urllib.parse import quote

import pytz
import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from player.models import TenhouNickname, TenhouStatistics
from utils.general import get_month_first_day, get_month_last_day
from utils.tenhou.latest_tenhou_games import lobbies_dict
from utils.tenhou.points_calculator import PointsCalculator


def get_date_string():
    return timezone.now().strftime('%H:%M:%S')


class Command(BaseCommand):

    def handle(self, *args, **options):
        print('{0}: Start'.format(get_date_string()))

        with transaction.atomic():
            TenhouStatistics.objects.all().delete()

            tenhou_objects = TenhouNickname.objects.all()

            for tenhou_object in tenhou_objects:
                load_data_for_tenhou_object(tenhou_object)

        print('{0}: End'.format(get_date_string()))


# they blocked my requests :(
def load_data_from_nodocchi(tenhou_object):
    url = 'https://nodocchi.moe/api/listuser.php?name={}'.format(
        quote(tenhou_object.tenhou_username, safe='')
    )
    print(url)

    response = requests.get(url).json()

    lobbies_dict = {
        '0': TenhouStatistics.KYU_LOBBY,
        '1': TenhouStatistics.DAN_LOBBY,
        '2': TenhouStatistics.UPPERDAN_LOBBY,
        '3': TenhouStatistics.PHOENIX_LOBBY,
    }

    lobbies_tenhou_dict = {
        '0': u'般',
        '1': u'上',
        '2': u'特',
        '3': u'鳳',
    }

    lobbies_data = {
        TenhouStatistics.KYU_LOBBY: {
            'all': {'played_games': 0, 1: 0, 2: 0, 3: 0, 4: 0},
            'current_month': {'played_games': 0, 1: 0, 2: 0, 3: 0, 4: 0}
        },
        TenhouStatistics.DAN_LOBBY: {
            'all': {'played_games': 0, 1: 0, 2: 0, 3: 0, 4: 0},
            'current_month': {'played_games': 0, 1: 0, 2: 0, 3: 0, 4: 0}
        },
        TenhouStatistics.UPPERDAN_LOBBY: {
            'all': {'played_games': 0, 1: 0, 2: 0, 3: 0, 4: 0},
            'current_month': {'played_games': 0, 1: 0, 2: 0, 3: 0, 4: 0}
        },
        TenhouStatistics.PHOENIX_LOBBY: {
            'all': {'played_games': 0, 1: 0, 2: 0, 3: 0, 4: 0},
            'current_month': {'played_games': 0, 1: 0, 2: 0, 3: 0, 4: 0}
        },
    }

    if response.get('rate'):
        four_games_rate = response.get('rate').get('4', None)
    else:
        four_games_rate = None

    games = response.get('list', [])

    month_first_day = get_month_first_day().date()
    month_last_day = get_month_last_day().date()

    player_games = []
    for game in games:
        if game['playernum'] != '4':
            continue

        # usual and phoenix games
        if game['sctype'] == 'b' or game['sctype'] == 'c':
            # api doesnt' return player place we had to assume from game results
            place = None
            for x in range(1, 5):
                if game['player{}'.format(x)] == tenhou_object.tenhou_username:
                    place = x
                    break

            if game['playlength'] == '1':
                game_type = u'東'
            else:
                game_type = u'南'

            date = datetime.utcfromtimestamp(int(game['starttime'])).replace(tzinfo=pytz.timezone('Asia/Tokyo')).date()

            lobby_name = lobbies_dict[game['playerlevel']]
            lobbies_data[lobby_name]['all']['played_games'] += 1
            lobbies_data[lobby_name]['all'][place] += 1

            if month_first_day <= date <= month_last_day:
                lobbies_data[lobby_name]['current_month']['played_games'] += 1
                lobbies_data[lobby_name]['current_month'][place] += 1

            player_games.append({
                'date': date,
                'place': place,
                'lobby': lobbies_tenhou_dict[game['playerlevel']],
                'game_type': game_type
            })

    update_stat(tenhou_object, lobbies_data, player_games)

    tenhou_object.four_games_rate = four_games_rate
    tenhou_object.save()


def update_stat(tenhou_object, lobbies_data, player_games, last_played_date):
    total_played_games = 0
    total_first_place = 0
    total_second_place = 0
    total_third_place = 0
    total_fourth_place = 0

    month_played_games = 0
    month_first_place = 0
    month_second_place = 0
    month_third_place = 0
    month_fourth_place = 0

    for lobby_key, lobby_data in lobbies_data.items():
        stat_types = {
            'all': TenhouStatistics.ALL_TIME,
            'current_month': TenhouStatistics.CURRENT_MONTH,
        }

        for key, stat_type in stat_types.items():
            if lobby_data[key]['played_games']:
                stat_object, _ = TenhouStatistics.objects.get_or_create(
                    lobby=lobby_key,
                    tenhou_object=tenhou_object,
                    stat_type=stat_type
                )

                games_count = lobby_data[key]['played_games']
                first_place = lobby_data[key][1]
                second_place = lobby_data[key][2]
                third_place = lobby_data[key][3]
                fourth_place = lobby_data[key][4]

                if stat_type == TenhouStatistics.ALL_TIME:
                    total_played_games += games_count
                    total_first_place += first_place
                    total_second_place += second_place
                    total_third_place += third_place
                    total_fourth_place += fourth_place
                else:
                    month_played_games += games_count
                    month_first_place += first_place
                    month_second_place += second_place
                    month_third_place += third_place
                    month_fourth_place += fourth_place

                average_place = (first_place + second_place * 2 + third_place * 3 + fourth_place * 4) / games_count

                first_place = (first_place / games_count) * 100
                second_place = (second_place / games_count) * 100
                third_place = (third_place / games_count) * 100
                fourth_place = (fourth_place / games_count) * 100

                stat_object.played_games = games_count
                stat_object.average_place = average_place
                stat_object.first_place = first_place
                stat_object.second_place = second_place
                stat_object.third_place = third_place
                stat_object.fourth_place = fourth_place
                stat_object.save()

    if total_played_games:
        total_average_place = (total_first_place + total_second_place * 2 + total_third_place * 3 + total_fourth_place * 4) / total_played_games
    else:
        total_average_place = 0

    if month_played_games:
        month_average_place = (month_first_place + month_second_place * 2 + month_third_place * 3 + month_fourth_place * 4) / month_played_games
    else:
        month_average_place = 0

    rank = PointsCalculator.calculate_rank(player_games)

    tenhou_object.rank = [x[0] for x in TenhouNickname.RANKS if x[1] == rank['rank']][0]
    tenhou_object.pt = rank['pt']
    tenhou_object.end_pt = rank['end_pt']
    tenhou_object.last_played_date = last_played_date
    tenhou_object.played_games = total_played_games
    tenhou_object.average_place = total_average_place
    tenhou_object.month_played_games = month_played_games
    tenhou_object.month_average_place = month_average_place
    tenhou_object.save()


def load_data_for_tenhou_object(tenhou_object):
    url = 'http://arcturus.su/tenhou/ranking/ranking.pl?name={}&d1={}'.format(
        quote(tenhou_object.tenhou_username, safe=''),
        tenhou_object.username_created_at.strftime('%Y%m%d'),
    )

    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser', from_encoding='utf-8')

    places_dict = {
        '1位': 1,
        '2位': 2,
        '3位': 3,
        '4位': 4,
    }

    lobbies_data = {
        TenhouStatistics.KYU_LOBBY: {
            'all': {'played_games': 0, 1: 0, 2: 0, 3: 0, 4: 0},
            'current_month': {'played_games': 0, 1: 0, 2: 0, 3: 0, 4: 0}
        },
        TenhouStatistics.DAN_LOBBY: {
            'all': {'played_games': 0, 1: 0, 2: 0, 3: 0, 4: 0},
            'current_month': {'played_games': 0, 1: 0, 2: 0, 3: 0, 4: 0}
        },
        TenhouStatistics.UPPERDAN_LOBBY: {
            'all': {'played_games': 0, 1: 0, 2: 0, 3: 0, 4: 0},
            'current_month': {'played_games': 0, 1: 0, 2: 0, 3: 0, 4: 0}
        },
        TenhouStatistics.PHOENIX_LOBBY: {
            'all': {'played_games': 0, 1: 0, 2: 0, 3: 0, 4: 0},
            'current_month': {'played_games': 0, 1: 0, 2: 0, 3: 0, 4: 0}
        },
    }

    records = soup.find('div', {'id': 'records'}).text.split('\n')
    player_games = []
    last_played_date = None
    for record in records:
        if not record:
            continue

        temp_array = record.strip().split('|')
        game_settings = temp_array[5].strip()

        place = places_dict[temp_array[0].strip()]
        lobby_number = temp_array[1].strip()
        lobby_name = lobbies_dict[game_settings[1]]
        game_type = game_settings[2]
        date = datetime.strptime(temp_array[3].strip(), '%Y-%m-%d').date()

        # for now let's collect stat only from usual games for 4 players
        if lobby_number == 'L0000' and game_settings[0] == u'四':
            lobbies_data[lobby_name]['all']['played_games'] += 1
            lobbies_data[lobby_name]['all'][place] += 1

            month_first_day = get_month_first_day().date()
            month_last_day = get_month_last_day().date()

            if month_first_day <= date <= month_last_day:
                lobbies_data[lobby_name]['current_month']['played_games'] += 1
                lobbies_data[lobby_name]['current_month'][place] += 1

            player_games.append({
                'date': date,
                'place': place,
                'lobby': game_settings[1],
                'game_type': game_type
            })

        last_played_date = date

    update_stat(tenhou_object, lobbies_data, player_games, last_played_date)
