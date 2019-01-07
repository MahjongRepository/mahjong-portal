import csv

from django.core.management.base import BaseCommand
from django.utils import timezone

from player.models import Player


class Command(BaseCommand):

    def handle(self, *args, **options):
        with open('export_players.csv', 'w') as f:
            writer = csv.writer(f)

            players = Player.all_objects.filter(country__code='RU')

            rows = [
                [
                    'id',
                    'last_name_ru',
                    'first_name_ru',
                    'last_name_en',
                    'first_name_en',
                    'ema_id',
                ]
            ]

            for player in players:
                rows.append([
                    player.id,
                    player.last_name_ru,
                    player.first_name_ru,
                    player.last_name_en,
                    player.first_name_en,
                    player.ema_id,
                ])

            for x in rows:
                writer.writerow(x)
