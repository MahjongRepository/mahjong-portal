import datetime
import os

import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from django.template.defaultfilters import floatformat

from rating.models import RatingResult, Rating


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--date', type=str)

    def handle(self, *args, **options):
        our_rating_date = options['date']
        our_rating_date = datetime.datetime.strptime(our_rating_date, '%Y-%m-%d')

        url = 'http://mahjong-europe.org/ranking/rcr.html'

        page = requests.get(url)
        soup = BeautifulSoup(page.content, 'html.parser', from_encoding='utf-8')

        date_block = soup.find('span', {'class': 'createdate'})
        if not date_block:
            print('no rating date')
            return

        try:
            rating_date = ' '.join([x.strip() for x in date_block.text.split(',')[1:]])
            rating_date = datetime.datetime.strptime(rating_date, '%B %d %Y').date()
        except Exception:
            print('Cant parse: {}'.format(date_block.text))
            return

        ranking_list = soup.findAll('div', {'class': 'Tableau_CertifiedTournament'})
        ranking_list = ranking_list[1]

        ema_players = {}
        results = ranking_list.findAll('div', {'class': ['TCTT_ligne', 'TCTT_ligneG']})
        for result in results:
            data = result.findAll('p')

            # header row
            if data[0].text.strip() == 'New':
                continue

            place = int(data[0].text.strip())
            ema_id = data[3].text.strip()
            last_name = data[4].text.strip().title()
            first_name = data[5].text.strip()
            scores = int(data[7].text.strip())

            if last_name == 'Wo&Zacute;Niak':
                last_name = 'Woźniak'

            country_code = os.path.basename(data[6].find('img')['src']).replace('.png', '').upper()

            ema_players[ema_id] = {
                'place': place,
                'last_name': last_name,
                'first_name': first_name,
                'scores': scores,
                'ema_id': ema_id,
                'country_code': country_code,
            }

        results = (RatingResult.objects
                   .filter(rating__type=Rating.EMA)
                   .filter(date=our_rating_date)
                   .prefetch_related('player', 'player__country')
                   .order_by('score'))

        if not results.exists():
            print('No rating results on {}'.format(our_rating_date))
            return

        players = {}
        for result in results:
            player = result.player
            players[player.ema_id] = {
                'place': result.place,
                'last_name': player.last_name_en,
                'first_name': player.first_name_en,
                'scores': int(floatformat(result.score, 0)),
                'ema_id': player.ema_id,
                'country_code': player.country.code,
            }

        missed = []
        for ema_id in reversed(list(ema_players.keys())):
            ema_player = ema_players[ema_id]

            if ema_id in players:
                player = players[ema_id]

                if player['scores'] != ema_player['scores']:
                    print('Not correct scores: {} {}. For {}'.format(
                        ema_player['scores'],
                        player['scores'],
                        format_player(ema_player)
                    ))

                if player['place'] != ema_player['place']:
                    print('Not correct place: {} {}. For {}'.format(
                        ema_player['place'],
                        player['place'],
                        format_player(ema_player)
                    ))

                if player['country_code'] != ema_player['country_code']:
                    print('Not correct country: {} {}. For {}'.format(
                        ema_player['country_code'],
                        player['country_code'],
                        format_player(ema_player)
                    ))

                if player['first_name'].title() != ema_player['first_name'].title() \
                        or player['last_name'].title() != ema_player['last_name'].title():
                    print('Names mismatch: id= {} {}'.format(
                        '{}'.format(ema_id),
                        'f= {} l= {}'.format(ema_player['first_name'], ema_player['last_name'])
                    ))
            else:
                missed.append(ema_player)

        print('')
        for player in missed:
            print('Missed player in our rating: {}'.format(format_player(player)))

        print('')
        for ema_id in players.keys():
            if ema_id not in ema_players:
                player = players[ema_id]
                print('User had to be removed from rating: {}'.format(format_player(player)))

        print('')
        print('EMA rating date: {}'.format(rating_date))
        print('Our rating date: {}'.format(our_rating_date))


def format_player(player):
    return '{} {} {}'.format(player['ema_id'], player['last_name'], player['first_name'])
