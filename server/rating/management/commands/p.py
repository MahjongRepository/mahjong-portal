import csv
import datetime
from time import sleep

import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand

from player.models import Player
from rating.calculation.ema import RatingEMACalculation
from tournament.models import Tournament, TournamentResult


class Command(BaseCommand):

    def handle(self, *args, **options):
        calculation = RatingEMACalculation()

        today = datetime.datetime.now().date()
        rating_date = today - datetime.timedelta(days=300)
        tournaments = Tournament.objects.filter(ema_id__isnull=False).filter(end_date__gte=rating_date).order_by('end_date')
        # tid=0
        # tournaments = Tournament.objects.filter(ema_id__isnull=False).filter(id__gte=tid).order_by('end_date')
        for tournament in tournaments:
            sleep(1)

            url = 'http://mahjong-europe.org/ranking/Tournament/TR_RCR_{}.html'.format(tournament.ema_id)
            print(url)
            page = requests.get(url)
            soup = BeautifulSoup(page.content, 'html.parser')

            table = soup.find('table')
            blocks = table.findAll('td')
            ema_coefficient = None
            ema_text = None
            for block in blocks:
                if 'Days=' in block.text:
                    ema_coefficient = float(block.text.split('(')[0].replace(',', '.'))
                    ema_text = block.text

            coefficient = calculation.tournament_coefficient(tournament)
            if coefficient != ema_coefficient:
                print(tournament.id)
                print(url)
                print('https://mahjong.click/en/tournaments/riichi/{}/'.format(tournament.slug))
                print(
                    '{}(Days={}, Countries={}, Players={}, Extra={})'.format(
                        calculation.tournament_coefficient(tournament),
                        calculation.duration_coefficient(tournament),
                        calculation.countries_coefficient(tournament),
                        calculation.players_coefficient(tournament),
                        calculation.qualification_coefficient(tournament)
                    ),
                )
                print(ema_text)

                ema_data = []
                table = soup.findAll('div', {'class': 'TCTT_lignes'})[0]
                # skip first row because it is a header
                results = table.findAll('div')[1:]
                for result in results:
                    data = result.findAll('p')

                    place = int(data[0].text.strip())
                    player_ema_id = data[1].text.strip().replace('-', '')
                    last_name = data[2].text.strip().title()
                    first_name = data[3].text.strip().title()
                    scores = data[6].text.strip().title()

                    if data[4].img:
                        country = data[4].img.attrs.get('src').replace('../Img/flag/16/', '').replace('.png', '').upper()
                    elif data[4].a:
                        country = data[4].a.attrs.get('href').replace('../Country/', '').replace('_Information.html', '').upper()
                    else:
                        country = None

                    if country == '-':
                        country = None

                    ema_data.append({
                        'country': country,
                        'ema_id': player_ema_id,
                        'place': place,
                        'last_name': last_name,
                        'first_name': first_name,
                    })

                results = TournamentResult.objects.filter(tournament=tournament)
                for result in results:
                    correspond = [x for x in ema_data if x['place'] == result.place]
                    if correspond:
                        correspond = correspond[0]
                        if not result.player or not result.player.country:
                            print('no country or player', correspond)
                        elif correspond['country'] != result.player.country.code:
                            print(correspond)
                    else:
                        print('not found')

                return
