# -*- coding: utf-8 -*-

import datetime
import os

import pytz
import requests
import ujson as json
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from player.tenhou.models import CollectedYakuman, TenhouNickname

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0"}


def get_date_string():
    return timezone.now().strftime("%H:%M:%S")


class Command(BaseCommand):
    def handle(self, *args, **options):
        print("{0}: Start".format(get_date_string()))

        tenhou_objects = TenhouNickname.active_objects.all().prefetch_related("player")
        player_profiles = {}
        for tenhou_object in tenhou_objects:
            player_profiles[tenhou_object.tenhou_username] = tenhou_object

        with transaction.atomic():
            self.old_records(player_profiles)
            self.current_month_data(player_profiles)

        print("{0}: End".format(get_date_string()))

    def current_month_data(self, player_profiles):
        url = "http://tenhou.net/sc/ykm.js"
        print(url)

        current_date = datetime.datetime.now().astimezone(pytz.timezone("Asia/Tokyo"))
        current_year = current_date.year
        data = requests.get(url, headers=headers).content.decode("utf-8")
        self.parse_and_create_records(player_profiles, data, current_year)

    def old_records(self, player_profiles):
        """
        Download historical data
        """
        current_date = datetime.datetime.now().astimezone(pytz.timezone("Asia/Tokyo"))
        current_year = current_date.year

        # 2006 - 2009 years have old format
        # we need to add additional support for them
        start_year = 2009
        stop_year = current_year
        months = ["{:02}".format(x) for x in range(1, 13)]

        folder = os.path.join("/tmp", "yakuman")
        if not os.path.exists(folder):
            os.mkdir(folder)

        for year in range(start_year, stop_year + 1):
            # we don't need to load data from the future
            if current_year == year:
                months = ["{:02}".format(x) for x in range(1, current_date.month)]

            for month in months:
                print(year, month)
                file_path = os.path.join(folder, "{}-{}.json".format(year, month))

                data = None
                # load from cache
                if os.path.exists(file_path):
                    with open(file_path, "r") as f:
                        data = f.read()
                else:
                    url = "http://tenhou.net/sc/{}/{}/ykm.js".format(year, month)
                    response = requests.get(url, headers=headers)

                    if response.status_code == 200:
                        data = response.content.decode("utf-8")
                        # store to cache
                        with open(file_path, "w") as f:
                            f.write(data)

                if not data:
                    print("Missed data")
                    continue

                self.parse_and_create_records(player_profiles, data, year)

    def parse_and_create_records(self, player_profiles, yakuman_data, year):
        # tenhou returns it not in really handy format

        # new format
        if "\r\n" in yakuman_data:
            yakuman_data = yakuman_data.split("\r\n")[2]
            yakuman_data = json.loads(yakuman_data[4:-1].replace('"', '\\"').replace("'", '"'))
        # old format
        else:
            yakuman_data = yakuman_data.split(";\n")[2].strip()
            yakuman_data = yakuman_data[4:].replace('"', '\\"').replace("'", '"').replace("\n", "")
            yakuman_data = json.loads(yakuman_data)

        filtered_results = []

        for x in range(0, len(yakuman_data), 5):
            yakuman_date = yakuman_data[x]
            name = yakuman_data[x + 1]
            yakuman_list = yakuman_data[x + 3]
            log = yakuman_data[x + 4]

            if name in player_profiles:
                date = "{} {}".format(year, yakuman_date)
                date = datetime.datetime.strptime(date, "%Y %m/%d %H:%M")
                date = date.astimezone(pytz.timezone("Asia/Tokyo"))

                tenhou_object = player_profiles[name]

                # let's add only yakumans related to the current profile
                if date.date() >= tenhou_object.username_created_at:
                    filtered_results.append(
                        {
                            "tenhou_object": tenhou_object,
                            "date": date,
                            "yakuman_list": ",".join([str(x) for x in yakuman_list]),
                            "log_id": log,
                        }
                    )

        for item in filtered_results:
            exists = (
                CollectedYakuman.objects.filter(tenhou_object=item["tenhou_object"]).filter(date=item["date"])
            ).exists()

            if not exists:
                CollectedYakuman.objects.create(**item)
