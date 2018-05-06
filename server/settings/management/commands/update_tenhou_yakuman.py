import json
import datetime

import pytz
import requests
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from player.models import TenhouNickname, CollectedYakuman
from utils.tenhou.latest_tenhou_games import get_latest_wg_games


def get_date_string():
    return timezone.now().strftime('%H:%M:%S')


class Command(BaseCommand):

    def handle(self, *args, **options):
        print('{0}: Start'.format(get_date_string()))

        tenhou_objects = TenhouNickname.objects.all().prefetch_related('player')
        player_profiles = {}
        for tenhou_object in tenhou_objects:
            player_profiles[tenhou_object.tenhou_username] = tenhou_object

        with transaction.atomic():
            # CollectedYakuman.objects.all().delete()
            #
            # self.old_records(player_profiles)
            self.current_month_data(player_profiles)

        print('{0}: End'.format(get_date_string()))

    def current_month_data(self, player_profiles):
        url = 'http://tenhou.net/sc/ykm.js'
        print(url)

        current_year = datetime.datetime.now().replace(tzinfo=pytz.timezone('Asia/Tokyo')).year
        response = requests.get(url)
        self.parse_and_create_records(player_profiles, response, current_year)

    def old_records(self, player_profiles):
        """
        Download historical data
        """
        # 2006 - 2009 years had old format
        # we need additionally support it
        start_year = 2009
        stop_year = timezone.now().year
        months = ['{:02}'.format(x) for x in range(1, 13)]

        for year in range(start_year, stop_year + 1):
            for month in months:
                url = 'http://tenhou.net/sc/{}/{}/ykm.js'.format(year, month)
                response = requests.get(url)

                if response.status_code == 200:
                    print(url)
                    self.parse_and_create_records(player_profiles, response, year)

    def parse_and_create_records(self, player_profiles, response, year):
        # tenhou returns it not in really handy format
        yakuman_data = response.content.decode('utf-8')
        # new format
        if '\r\n' in yakuman_data:
            yakuman_data = response.content.decode('utf-8').split('\r\n')[2]
            yakuman_data = json.loads(yakuman_data[4:-1].replace('"', '\\"').replace("'", '"'))
        # old format
        else:
            yakuman_data = yakuman_data.split(';\n')[2]
            yakuman_data = yakuman_data[4:].replace('"', '\\"').replace("'", '"').replace('\n', '')
            yakuman_data = json.loads(yakuman_data)

        filtered_results = []

        for x in range(0, len(yakuman_data), 5):
            yakuman_date = yakuman_data[x]
            name = yakuman_data[x + 1]
            yakuman_list = yakuman_data[x + 3]
            log = yakuman_data[x + 4]

            if name in player_profiles:
                date = '{} {}'.format(year, yakuman_date)
                date = datetime.datetime.strptime(date, '%Y %m/%d %H:%M')
                date = date.replace(tzinfo=pytz.timezone('Asia/Tokyo'))

                filtered_results.append({
                    'tenhou_object': player_profiles[name],
                    'date': date,
                    'yakuman_list': ','.join([str(x) for x in yakuman_list]),
                    'log_id': log
                })

        for item in filtered_results:
            exists = (CollectedYakuman.objects
                      .filter(tenhou_object=item['tenhou_object'])
                      .filter(date=item['date'])).exists()

            if not exists:
                CollectedYakuman.objects.create(**item)
