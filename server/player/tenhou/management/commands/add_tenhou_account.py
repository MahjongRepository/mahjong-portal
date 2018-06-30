from datetime import datetime
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from django.utils import timezone

from player.models import Player
from player.tenhou.management.commands.download_all_games import download_all_games_from_arcturus
from player.tenhou.models import TenhouNickname


def get_date_string():
    return timezone.now().strftime('%H:%M:%S')


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('player_name', type=str)
        parser.add_argument('tenhou_nickname', type=str)

    def handle(self, *args, **options):
        print('{0}: Start'.format(get_date_string()))

        temp = options.get('player_name').split(' ')
        last_name = temp[0]
        first_name = temp[1]

        player = Player.objects.get(first_name_ru=first_name, last_name_ru=last_name)
        tenhou_nickname = options.get('tenhou_nickname')

        url = 'http://arcturus.su/tenhou/ranking/ranking.pl?name={}'.format(
            quote(tenhou_nickname, safe='')
        )

        page = requests.get(url)
        soup = BeautifulSoup(page.content, 'html.parser', from_encoding='utf-8')

        previous_date = None
        account_start_date = None

        records = soup.find('div', {'id': 'records'}).text.split('\n')
        for record in records:
            if not record:
                continue

            temp_array = record.strip().split('|')
            date = datetime.strptime(temp_array[3].strip(), '%Y-%m-%d')

            # let's initialize start date with first date in the list
            if not account_start_date:
                account_start_date = date

            if previous_date:
                delta = date - previous_date
                # it means that account wasn't used long time and was wiped
                if delta.days > 180:
                    account_start_date = date

            previous_date = date

        tenhou_object = TenhouNickname.objects.create(
            player=player,
            tenhou_username=tenhou_nickname,
            rank=TenhouNickname.RANKS[0][0],
            username_created_at=account_start_date
        )

        download_all_games_from_arcturus(tenhou_object)

        print('{0}: End'.format(get_date_string()))
