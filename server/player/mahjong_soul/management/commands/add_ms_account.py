from django.core.management import BaseCommand

from player.mahjong_soul.models import MSAccount
from player.models import Player


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('player_name', type=str)
        parser.add_argument('ms_id', type=str)

    def handle(self, *args, **options):
        temp = options.get('player_name').split(' ')
        last_name = temp[0]
        first_name = temp[1]

        player = Player.objects.get(first_name_ru=first_name, last_name_ru=last_name)
        ms_id = options.get('ms_id')

        MSAccount.objects.get_or_create(player=player, account_id=ms_id)
