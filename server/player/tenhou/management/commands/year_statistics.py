from django.core.management.base import BaseCommand
from datetime import datetime

import pytz
from django.db.models import Sum

from player.models import Player
from player.tenhou.models import TenhouGameLog
from settings.models import City
from tournament.models import TournamentResult, Tournament


class Command(BaseCommand):

    def handle(self, *args, **options):
        start_date = datetime(2018, 1, 1, tzinfo=pytz.UTC)
        end_date = datetime(2019, 1, 1, tzinfo=pytz.UTC)

        results = TournamentResult.objects.filter(
            tournament__end_date__gte=start_date,
            tournament__end_date__lt=end_date,
        ).exclude(tournament__tournament_type=Tournament.FOREIGN_EMA)

        player_ids = [x.player_id for x in results]
        players = Player.objects.filter(id__in=player_ids).distinct()
        print('Players: {}'.format(players.count()))

        city_ids = [x.city.id for x in players if x.city]
        cities = City.objects.filter(id__in=city_ids)
        print('Cities: {}'.format(cities.count()))

        games = TenhouGameLog.objects.filter(game_date__gte=start_date, game_date__lt=end_date)
        print('Games: {}'.format(games.count()))

        sum_minutes = games.aggregate(Sum('game_length'))['game_length__sum']

        print('Hours: {}, Days: {}'.format(sum_minutes / 60, sum_minutes / 60 / 24))

        lobbies_dict = {
            '般': {
                'name': 'Кю лобби',
                'up_points': 0,
                'down_points': 0,
            },
            '上': {
                'name': 'Перводан',
                'up_points': 0,
                'down_points': 0,
            },
            '特': {
                'name': 'Втородан',
                'up_points': 0,
                'down_points': 0,
            },
            '鳳': {
                'name': 'Феникс',
                'up_points': 0,
                'down_points': 0,
            },
        }

        up_dans = 0
        downgrade_dans = 0

        for game in games:
            if game.rank and game.next_rank and game.rank != game.next_rank:
                if game.next_rank > game.rank:
                    up_dans += 1
                else:
                    downgrade_dans += 1

            stat_item = lobbies_dict[game.game_rules[1]]

            if game.delta > 0:
                stat_item['up_points'] += game.delta
            else:
                stat_item['down_points'] += game.delta * -1

        print('Up dans: {}'.format(up_dans))
        print('Downgrade dans: {}'.format(downgrade_dans))

        for item in lobbies_dict.values():
            print('')
            print(item['name'])
            print('Up points: {}'.format(item['up_points']))
            print('Down points: {}'.format(item['down_points']))
            print('Balance: {}'.format(item['up_points'] - item['down_points']))
