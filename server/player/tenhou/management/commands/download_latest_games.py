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

from player.tenhou.models import TenhouNickname, TenhouGameLog
from utils.tenhou.current_tenhou_games import lobbies_dict
from utils.tenhou.helper import parse_log_line, recalculate_tenhou_statistics_for_four_players


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
        if not os.path.exists(temp_folder):
            os.mkdir(temp_folder)

        archive_names = self.download_archives_with_games(temp_folder, settings.TENHOU_LATEST_GAMES_URL)
        lines = self.load_game_records(temp_folder, archive_names)

        for line in lines:
            date = line[0]
            result = parse_log_line(line[1])
            for player in result['players']:
                # player from watched list
                # was found in latest games
                if player['name'] in watching_nicknames:
                    # skip sanma games for now
                    if result['game_rules'][0] == u'三':
                        continue

                    game_date = '{} {} +0900'.format(date.strftime('%Y-%d-%m'), result['game_time'])
                    game_date = datetime.strptime(game_date, '%Y-%d-%m %H:%M %z')

                    results.append({
                        'name': player['name'],
                        'place': player['place'],
                        'game_rules': result['game_rules'],
                        'game_length': result['game_length'],
                        'game_date': game_date
                    })

        added_accounts = {}
        with transaction.atomic():
            for result in results:
                tenhou_object = cached_objects[result['name']]

                TenhouGameLog.objects.get_or_create(
                    tenhou_object=tenhou_object,
                    place=result['place'],
                    game_date=result['game_date'],
                    game_rules=result['game_rules'],
                    game_length=result['game_length'],
                    lobby=lobbies_dict[result['game_rules'][1]]
                )

                added_accounts[tenhou_object.id] = tenhou_object

            for tenhou_object in added_accounts.values():
                recalculate_tenhou_statistics_for_four_players(tenhou_object)

        print('{0}: End'.format(get_date_string()))

    def download_archives_with_games(self, logs_folder, items_url):
        download_url = settings.TENHOU_DOWNLOAD_ARCHIVE_URL

        response = requests.get(items_url)
        response = response.text.replace('list(', '').replace(');', '')
        response = response.split(',\r\n')

        archive_names = []
        for item in response:
            # scb are games from 0000 lobby
            if 'scb' in item:
                archive_name = item.split("',")[0].replace("{file:'", '')
                archive_names.append(archive_name)

        processed = []
        for i, archive_name in enumerate(archive_names):
            file_name = archive_name
            if '/' in file_name:
                file_name = file_name.split('/')[1]

            archive_path = os.path.join(logs_folder, file_name)

            download = not os.path.exists(archive_path)
            # because of tenhou format we need to download latest two data files each run
            if (i + 1 == len(archive_names)) or (i + 2 == len(archive_names)):
                download = True

            if download:
                print('Downloading... {}'.format(archive_name))

                url = '{}{}'.format(download_url, archive_name)
                page = requests.get(url)
                with open(archive_path, 'wb') as f:
                    f.write(page.content)

                processed.append(archive_name)

        return processed

    def load_game_records(self, logs_folder, archive_names):
        lines = []
        for file_name in archive_names:
            gz_file = os.path.join(logs_folder, file_name)
            date = datetime.strptime(file_name[3:11], '%Y%m%d')
            with gzip.open(gz_file, 'r') as f:
                for line in f:
                    lines.append([
                        date,
                        line.decode('utf-8')
                    ])
        return lines
