
from django.core.management.base import BaseCommand
from django.utils import timezone

from player.tenhou.models import TenhouNickname
from utils.tenhou.current_tenhou_games import get_latest_wg_games


def get_date_string():
    return timezone.now().strftime('%H:%M:%S')


class Command(BaseCommand):

    def handle(self, *args, **options):
        print('{0}: Start'.format(get_date_string()))

        games = get_latest_wg_games()

        tenhou_objects = TenhouNickname.objects.all().prefetch_related('player')
        player_profiles = {}
        for tenhou_object in tenhou_objects:
            player_profiles[tenhou_object.tenhou_username] = tenhou_object

        found_players = {}
        for game in games:
            for player in game['players']:
                # we found a player from our database
                # and this is not hirosima
                if len(game['players']) == 4 and player['name'] in player_profiles:
                    found_players[player['name']] = player['rate']

        for player_name, rate in found_players.items():
            tenhou_obj = player_profiles[player_name]
            tenhou_obj.four_games_rate = rate
            tenhou_obj.save()

        print('{0}: End'.format(get_date_string()))
