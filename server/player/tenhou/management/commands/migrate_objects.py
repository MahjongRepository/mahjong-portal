from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from player.tenhou.models import TenhouGameLog, TenhouNickname, TenhouAggregatedStatistics


def get_date_string():
    return timezone.now().strftime('%H:%M:%S')


class Command(BaseCommand):

    def handle(self, *args, **options):
        print('{0}: Start'.format(get_date_string()))

        with transaction.atomic():
            TenhouGameLog.objects.all().update(game_players=TenhouGameLog.FOUR_PLAYERS)

            tenhou_objects = TenhouNickname.objects.all()
            for tenhou_object in tenhou_objects:
                TenhouAggregatedStatistics.objects.create(
                    game_players=TenhouAggregatedStatistics.FOUR_PLAYERS,
                    tenhou_object=tenhou_object,
                    rank=tenhou_object.rank,
                    rate=tenhou_object.four_games_rate,
                    played_games=tenhou_object.played_games,
                    month_played_games=tenhou_object.month_played_games,
                    average_place=tenhou_object.average_place,
                    month_average_place=tenhou_object.month_average_place,
                    pt=tenhou_object.pt,
                    end_pt=tenhou_object.end_pt
                )

        print('{0}: End'.format(get_date_string()))
