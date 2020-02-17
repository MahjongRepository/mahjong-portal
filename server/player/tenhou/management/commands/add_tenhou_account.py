from django.core.management.base import BaseCommand
from django.utils import timezone

from player.models import Player
from player.tenhou.models import TenhouNickname
from utils.tenhou.helper import recalculate_tenhou_statistics_for_four_players, download_all_games_from_arcturus, \
    save_played_games, get_started_date_for_account


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
        account_start_date = get_started_date_for_account(tenhou_nickname)

        is_main = TenhouNickname.objects.filter(player=player, is_active=True).count() == 0
        tenhou_object = TenhouNickname.objects.create(
            is_main=is_main,
            player=player,
            tenhou_username=tenhou_nickname,
            rank=TenhouNickname.RANKS[0][0],
            username_created_at=account_start_date
        )

        player_games = download_all_games_from_arcturus(
            tenhou_object.tenhou_username,
            tenhou_object.username_created_at
        )
        save_played_games(tenhou_object, player_games)

        recalculate_tenhou_statistics_for_four_players(tenhou_object, player_games)

        print('{0}: End'.format(get_date_string()))
