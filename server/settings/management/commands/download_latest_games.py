import glob
import gzip
import os
import shutil
from datetime import datetime

import requests
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from player.models import TenhouNickname, TenhouGameLog
from utils.tenhou.latest_tenhou_games import lobbies_dict
from utils.tenhou.load_latest_games import parse_log_line, generate_game_hash


def get_date_string():
    return timezone.now().strftime('%H:%M:%S')


class Command(BaseCommand):

    def handle(self, *args, **options):
        print('{0}: Start'.format(get_date_string()))

        tenhou_objects = TenhouNickname.objects.all()
        watching_nicknames = []
        cached_objects = {}
        for obj in tenhou_objects:
            watching_nicknames.append(obj.tenhou_username)
            cached_objects[obj.tenhou_username] = obj

        results = []

        temp_folder = os.path.join('/tmp', 'tenhou')
        # shutil.rmtree(temp_folder, ignore_errors=True)
        # os.mkdir(temp_folder)

        # self.download_archives_with_games(temp_folder, settings.TENHOU_LATEST_GAMES_URL)
        lines = self.load_game_records(temp_folder)

        for line in lines:
            date = line[0]
            result = parse_log_line(line[1])
            for player in result['players']:
                # player from watched list
                # was found in latest games
                if player['name'] in watching_nicknames:
                    game_date = '{} {} +0900'.format(date.strftime('%Y-%d-%m'), result['game_time'])
                    results.append({
                        'name': player['name'],
                        'position': player['position'],
                        'game_type': result['game_type'],
                        'game_date': game_date
                    })

        items_to_create = []
        with transaction.atomic():
            for result in results:
                items_to_create.append(TenhouGameLog(
                    tenhou_object=cached_objects[result['name']],
                    game_date=result['game_date'],
                    game_rules=result['game_type'],
                    lobby=lobbies_dict[result['game_type'][1]]
                ))

        TenhouGameLog.objects.bulk_create(items_to_create)

        print('{0}: End'.format(get_date_string()))

    def download_archives_with_games(self, logs_folder, items_url):
        download_url = 'http://tenhou.net/sc/raw/dat/'

        response = requests.get(items_url)
        response = response.text.replace('list(', '').replace(');', '')
        response = response.split(',\r\n')
        for archive_name in response:
            # scb is games from 0000 lobby
            if 'scb' in archive_name:
                archive_name = archive_name.split("',")[0].replace("{file:'", '')

                file_name = archive_name
                if '/' in file_name:
                    file_name = file_name.split('/')[1]
                archive_path = os.path.join(logs_folder, file_name)

                if not os.path.exists(archive_path):
                    print('Downloading... {}'.format(archive_name))

                    url = '{}{}'.format(download_url, archive_name)
                    page = requests.get(url)
                    with open(archive_path, 'wb') as f:
                        f.write(page.content)

    def load_game_records(self, logs_folder):
        gz_files = glob.glob('{}/*.gz'.format(logs_folder))
        lines = []
        for gz_file in gz_files:
            file_name = gz_file.split('/')[-1]
            date = datetime.strptime(file_name[3:11], '%Y%m%d')
            with gzip.open(gz_file, 'r') as f:
                for line in f:
                    lines.append([
                        date,
                        line.decode('utf-8')
                    ])
        return lines
