from datetime import datetime
from urllib.parse import quote

import pytz
import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from player.tenhou.models import TenhouStatistics, TenhouNickname, TenhouGameLog
from utils.general import get_month_first_day, get_month_last_day
from utils.tenhou.current_tenhou_games import lobbies_dict
from utils.tenhou.helper import recalculate_tenhou_statistics
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
                download_all_games_from_arcturus(tenhou_object)
                recalculate_tenhou_statistics(tenhou_object)

        print('{0}: End'.format(get_date_string()))


def download_all_games_from_arcturus(tenhou_object):
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

    records = soup.find('div', {'id': 'records'}).text.split('\n')
    player_games = []
    for record in records:
        if not record:
            continue

        temp_array = record.strip().split('|')
        game_rules = temp_array[5].strip()[:-1]

        place = places_dict[temp_array[0].strip()]
        lobby_number = temp_array[1].strip()

        # let's collect stat only from usual games for 4 players
        if lobby_number == 'L0000' and game_rules[0] == u'四':
            game_length = int(temp_array[2].strip())
            date = temp_array[3].strip()
            time = temp_array[4].strip()
            date = datetime.strptime('{} {} +0900'.format(date, time), '%Y-%m-%d %H:%M %z')

            player_games.append({
                'place': place,
                'game_rules': game_rules,
                'game_length': game_length,
                'game_date': date,
            })

    with transaction.atomic():
        for result in player_games:
            TenhouGameLog.objects.get_or_create(
                tenhou_object=tenhou_object,
                place=result['place'],
                game_date=result['game_date'],
                game_rules=result['game_rules'],
                game_length=result['game_length'],
                lobby=lobbies_dict[result['game_rules'][1]]
            )
