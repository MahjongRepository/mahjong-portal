import csv
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify

from player.models import Player
from settings.models import Country, City
from tournament.models import Tournament, TournamentResult


def get_date_string():
    return timezone.now().strftime('%H:%M:%S')


class Command(BaseCommand):
    countries = [
        'RUS', 'DEN', 'NED', 'FRA', 'POL', 'GER', 'GBR', 'AUT', 'SVK', 'FIN',
        'UKR', 'SWE', 'CZE', 'ITA', 'BLR', 'SUI', 'BEL', 'HUN'
    ]

    tournaments_file = 'tournaments.csv'
    results_file = 'results.csv'

    def handle(self, *args, **options):
        print('{0}: Start'.format(get_date_string()))

        # self.download_tournaments_list()
        self.download_tournaments_results()
        # self.import_data()

        print('{0}: End'.format(get_date_string()))

    def import_data(self):
        tournaments = {}
        players = {}

        cities = []
        countries = []

        countries_map = {
            'AUT': 'AT',
            'BEL': 'BE',
            'BLR': 'BY',
            'CZE': 'CZ',
            'DEN': 'DK',
            'ESP': 'ES',
            'FIN': 'FI',
            'FRA': 'FR',
            'GBR': 'GB',
            'GER': 'DE',
            'HUN': 'HU',
            'ITA': 'IT',
            'NED': 'NL',
            'POL': 'PL',
            'POR': 'PT',
            'RUS': 'RU',
            'SUI': 'CH',
            'SVK': 'SK',
            'SWE': 'SE',
            'UKR': 'UA',
        }

        with open(self.tournaments_file, 'r') as f:
            reader = csv.DictReader(f, delimiter=',')

            for row in reader:
                tournament_id = row['tournament_id']
                current_id = row['current_id']
                start_date = row['start_date']
                end_date = row['end_date']
                city = row['city'].strip().title()
                country = row['country']
                name = row['name']

                if city and city not in cities:
                    cities.append(city)

                if country in countries_map:
                    country = countries_map[country]

                if tournament_id in tournaments:
                    print('Tournament {} already exists'.format(tournament_id))

                tournaments[tournament_id] = {
                    'tournament_id': tournament_id,
                    'current_id': current_id,
                    'start_date': start_date,
                    'end_date': end_date,
                    'city': city,
                    'country': country,
                    'name': name,
                    'results': []
                }

        with open(self.results_file, 'r') as f:
            reader = csv.DictReader(f, delimiter=',')

            for row in reader:
                tournament_id = row['tournament_id']
                place = row['place']
                first_name = row['first_name']
                last_name = row['last_name']
                scores = row['scores']
                country = row['country'].upper()
                ema_id = row['ema_id']

                if country in countries_map:
                    country = countries_map[country]

                if country and country not in countries:
                    countries.append(country)

                slug = '{} {}'.format(last_name, first_name)

                if slug in players:
                    # add additional information
                    if not players[slug]['ema_id'] and ema_id:
                        players[slug]['ema_id'] = ema_id

                    if players[slug]['ema_id'] and ema_id and players[slug]['ema_id'] != ema_id:
                        print('Not consistent ema id for player')
                        print(players[slug]['ema_id'], ema_id)
                        print(slug)

                    # add additional information
                    if not players[slug]['country'] and country:
                        players[slug]['country'] = country

                    if players[slug]['country'] and country and players[slug]['country'] != country:
                        print('Not consistent country for player')
                        print(players[slug]['country'], country)
                        print(slug)
                else:
                    players[slug] = {
                        'first_name': first_name,
                        'last_name': last_name,
                        'country': country,
                        'ema_id': ema_id
                    }

                tournaments[tournament_id]['results'].append({
                    'player': slug,
                    'place': place,
                    'scores': scores
                })

        for player_slug in players.keys():
            player = players[player_slug]

            if player['country'] == 'RU':
                try:
                    Player.all_objects.get(last_name_en=player['last_name'], first_name_en=player['first_name'])
                except Player.DoesNotExist:
                    print('Missed russian player {} {}'.format(player['last_name'], player['first_name']))

        cities_objects = {}
        country_objects = {}
        player_objects = {}

        for country in countries:
            try:
                country_obj = Country.objects.get(code=country)
            except Country.DoesNotExist:
                country_obj = Country.objects.create(
                    code=country,
                    name_en=country,
                    name_ru=country,
                )

            country_objects[country] = country_obj

        for city in cities:
            try:
                city_obj = City.objects.get(name_en=city)
            except City.DoesNotExist:
                city_obj = City.objects.create(
                    name_en=city,
                    name_ru=city,
                    slug=slugify(city)
                )

            cities_objects[city] = city_obj

        for player_slug in players.keys():
            player = players[player_slug]

            player_obj = None
            if 'player' in player['first_name'].lower() or 'player' in player['last_name'].lower():
                player_obj = Player.all_objects.get(is_replacement=True)

            if not player_obj:
                try:
                    player_obj = Player.all_objects.get(last_name_en=player['last_name'], first_name_en=player['first_name'])
                except Player.DoesNotExist:
                    player_obj = Player.objects.create(
                        first_name_ru=player['first_name'],
                        first_name_en=player['first_name'],
                        last_name_ru=player['last_name'],
                        last_name_en=player['last_name'],
                        slug=slugify('{} {}'.format(player['last_name'], player['first_name'])),
                        ema_id=player['ema_id'],
                        country=player['country'] and country_objects[player['country']] or None,
                    )

            player_objects[player_slug] = player_obj

        for tournament_slug in tournaments.keys():
            tournament = tournaments[tournament_slug]

            if tournament['current_id']:
                tournament_obj = Tournament.objects.get(id=tournament['current_id'])
                tournament_obj.name = tournament['name']
                tournament_obj.ema_id = tournament['tournament_id']
                tournament_obj.save()
                # we don't need to import results for already added tournaments
                continue

            tournament_obj = Tournament.objects.create(
                slug=slugify(tournament['name']),
                name_en=tournament['name'],
                name_ru=tournament['name'],
                number_of_sessions=0,
                ema_id=tournament['tournament_id'],
                start_date=datetime.strptime(tournament['start_date'], '%m/%d/%Y'),
                end_date=datetime.strptime(tournament['end_date'], '%m/%d/%Y'),
                tournament_type_new=Tournament.FOREIGN_EMA,
                city=tournament['city'] and cities_objects[tournament['city']] or None,
                country=country_objects[tournament['country']],
                number_of_players=len(tournament['results'])
            )

            for tournament_result in tournament['results']:
                TournamentResult.objects.create(
                    player=player_objects[tournament_result['player']],
                    tournament=tournament_obj,
                    place=tournament_result['place'],
                    scores=tournament_result['scores'] and int(tournament_result['scores']) or 0,
                )

    def download_tournaments_results(self):
        with open(self.tournaments_file, 'r') as f:
            reader = csv.DictReader(f, delimiter=',')

            writer = csv.writer(open(self.results_file, 'w+'))
            writer.writerow(['tournament_id', 'place', 'first_name', 'last_name', 'scores', 'country', 'ema_id'])

            for row in reader:
                print('Processing {}...'.format(row['tournament_id']))

                tournament_id = row['tournament_id']

                url = 'http://mahjong-europe.org/ranking/Tournament/TR_RCR_{}.html'.format(tournament_id)
                page = requests.get(url)
                soup = BeautifulSoup(page.content, 'html.parser')

                # table = soup.find_all('table')[0]
                # rows = table.findAll('tr')
                # text = rows[-2].findAll('td')[1].text
                # print(tournament_id, text)

                table = soup.findAll('div', {'class': 'TCTT_lignes'})[0]
                # skip first row because it is a header
                results = table.findAll('div')[1:]
                for result in results:
                    data = result.findAll('p')

                    place = data[0].text.strip()
                    player_ema_id = data[1].text.strip().replace('-', '')
                    last_name = data[2].text.strip().title()
                    first_name = data[3].text.strip().title()
                    scores = data[6].text.strip().title()

                    if first_name == 'Masahiko Takahashi':
                        first_name = 'Masahiko'
                        last_name = 'Takahashi'

                    if last_name == '-':
                        t = first_name.split(' ')
                        first_name = ' '.join(t[0:-1])
                        last_name = t[-1]

                    if scores == '1' or scores == 'N/A' or scores == '0':
                        scores = ''

                    if data[4].a:
                        country = data[4].a.attrs.get('href').replace('../Country/', '').replace('_Information.html', '')
                    elif data[4].img:
                        country = data[4].img.attrs.get('src').replace('../Img/flag/16/', '').replace('.png', '')
                    else:
                        country = None

                    if country == '-':
                        country = None

                    writer.writerow([
                        tournament_id,
                        place,
                        first_name,
                        last_name,
                        scores,
                        country or '',
                        player_ema_id
                    ])

    def download_tournaments_list(self):
        # first number is ema id
        # second number is our tournament id
        already_added_tournaments = {
            '180': '87',
            '177': '76',
            '171': '62',
            '168': '43',
            '160': '57',
            '158': '24',
            '146': '74',
            '137': '44',
            '120': '25',
            '113': '8',
            '106': '52',
            '96': '45',
            '92': '46',
            '95': '77',
            '67': '78',
            '87': '13',
            '73': '49',
            '68': '48',
            '51': '75',
        }

        writer = csv.writer(open(self.tournaments_file, 'w+'))
        writer.writerow(['tournament_id', 'current_id', 'start_date', 'end_date', 'city', 'country', 'name'])

        for country in self.countries:
            print('Processing {}...'.format(country))

            url = 'http://mahjong-europe.org/ranking/Country/{}_Information.html'.format(country)

            page = requests.get(url)
            soup = BeautifulSoup(page.content, 'html.parser')

            results = soup.findAll('div', {'class': 'TCTT_ligneRiichi'})
            for result in results:
                data = result.findAll('p')

                date = data[1].text.strip()
                city = data[2].text.strip().title()
                name = data[3].text.strip()

                url = data[3].a.attrs.get('href')
                ema_id = re.findall(r'\d+', url)[0]

                date_format = '%d %b %Y'

                # source dates have different formats,
                # so let's unify dates string
                date = date.replace('.', '')
                date = date.replace('Sept', 'Sep')
                date = date.replace('sept', 'Sep')
                date = date.replace('April', 'Apr')
                date = date.replace('april', 'Apr')
                date = date.replace('August', 'Aug')
                date = date.replace('June', 'Jun')
                date = date.replace('July', 'Jul')
                date = date.replace('March', 'Mar')

                if date == '31 Jan 1 Feb 2015':
                    start_date = datetime.strptime('31 Jan 2015', date_format)
                    end_date = datetime.strptime('1 Feb 2015', date_format)
                elif date == '28 feb - 1 mar 2015':
                    start_date = datetime.strptime('28 Feb 2015', date_format)
                    end_date = datetime.strptime('1 Mar 2015', date_format)
                elif date == '25/10/2014':
                    start_date = datetime.strptime(date, '%d/%m/%Y')
                    end_date = start_date
                elif date == '17-mars-13':
                    start_date = datetime.strptime('17 Mar 2013', date_format)
                    end_date = start_date
                elif '-' in date:
                    # 2-3 Nov 2013
                    temp = date.split('-')
                    end_date_temp = temp[1].split(' ')

                    start_date = ' '.join([temp[0]] + end_date_temp[1:])
                    end_date = ' '.join(end_date_temp)

                    start_date = datetime.strptime(start_date, date_format)
                    end_date = datetime.strptime(end_date, date_format)
                else:
                    start_date = datetime.strptime(date, date_format)
                    end_date = start_date

                writer.writerow([
                    ema_id,
                    already_added_tournaments.get(ema_id) or '',
                    start_date.strftime('%m/%d/%Y'),
                    end_date.strftime('%m/%d/%Y'),
                    city,
                    country,
                    name,
                ])
