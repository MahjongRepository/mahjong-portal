# -*- coding: utf-8 -*-
from time import sleep

from django.core.management.base import BaseCommand
from django.utils import timezone

from player.tenhou.models import TenhouNickname
from player.tenhou.tenhou_helper import TenhouHelper


def get_date_string():
    return timezone.now().strftime("%H:%M:%S")


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--nickname", default=None, type=str)
        parser.add_argument("--rebuild-from-zero", default=False, type=bool)
        parser.add_argument("--with-curl", default=False, type=bool)

    def is_need_update(self, now, tenhou_object) -> bool:
        if tenhou_object.last_recalculated_date is not None:
            return now.toordinal() - tenhou_object.last_recalculated_date.toordinal() > 0
        else:
            return True

    def handle(self, *args, **options):
        tenhou_nickname = options.get("nickname")
        rebuild_from_zero = options.get("rebuild_from_zero")
        with_pycurl = options.get("with_curl")
        print("{0}: Start".format(get_date_string()))

        if tenhou_nickname:
            tenhou_objects = TenhouNickname.active_objects.filter(tenhou_username=tenhou_nickname)
        else:
            tenhou_objects = TenhouNickname.active_objects.all()
        tenhou_players_count = tenhou_objects.count()
        current_player_index = 1
        now = timezone.now()
        for tenhou_object in tenhou_objects:
            print(f"[{current_player_index}/{tenhou_players_count}] Processing {tenhou_object.tenhou_username}")
            if rebuild_from_zero or (rebuild_from_zero is False and self.is_need_update(now, tenhou_object)):
                TenhouHelper.recalculate_tenhou_account(tenhou_object, now, with_pycurl)

                # let's be gentle and don't ddos nodochi
                sleep(10)
            else:
                print("already updated, skipped...")
            current_player_index = current_player_index + 1
        print("{0}: End".format(get_date_string()))
