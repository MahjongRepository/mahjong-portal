from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from player.tenhou.models import TenhouNickname, TenhouStatistics
from utils.tenhou.helper import (
    download_all_games_from_arcturus,
    recalculate_tenhou_statistics_for_four_players,
    save_played_games,
)


def get_date_string():
    return timezone.now().strftime("%H:%M:%S")


class Command(BaseCommand):
    def handle(self, *args, **options):
        print("{0}: Start".format(get_date_string()))

        with transaction.atomic():
            TenhouStatistics.objects.all().delete()

            tenhou_objects = TenhouNickname.objects.all()

            for tenhou_object in tenhou_objects:
                player_games = download_all_games_from_arcturus(
                    tenhou_object.tenhou_username, tenhou_object.username_created_at
                )

                save_played_games(tenhou_object, player_games)
                recalculate_tenhou_statistics_for_four_players(tenhou_object, player_games)

        print("{0}: End".format(get_date_string()))
