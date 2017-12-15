import csv
import os

from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify
from unidecode import unidecode

from club.models import Club
from player.models import Player
from settings.models import Country, City, TournamentType
from tournament.models import Tournament, TournamentResult


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('dir')

    def handle(self, *args, **options):
        print('Start', end='\n\n')

        TournamentResult.objects.all().delete()

        Player.objects.all().delete()
        Tournament.objects.all().delete()
        Club.objects.all().delete()

        Country.objects.all().delete()
        City.objects.all().delete()
        TournamentType.objects.all().delete()

        csv_dir = options.get('dir')

        players_csv = os.path.join(csv_dir, 'players.csv')
        hidden_players_csv = os.path.join(csv_dir, 'hidden_players.csv')
        clubs_csv = os.path.join(csv_dir, 'clubs.csv')
        tournaments_csv = os.path.join(csv_dir, 'tournaments.csv')
        results_csv = os.path.join(csv_dir, 'results.csv')

        self.players = {}
        self.clubs = {}
        self.tournaments = {}
        self.countries = []
        self.cities = []

        print('Process players...')

        with open(players_csv, 'r') as f:
            reader = csv.DictReader(f, delimiter=',')

            for row in reader:
                data = self.process_player(row)
                self.players[data['name']] = data

        # some players chosen to be hidden from rating
        with open(hidden_players_csv, 'r') as f:
            reader = csv.DictReader(f, delimiter=',')

            for row in reader:
                data = self.process_player(row)
                data['is_hide'] = True
                self.players[data['name']] = data

        self.players['игрок замены'] = {
            'name': 'игрок замены',
            'first_name_ru': 'замены',
            'last_name_ru': 'Игрок',
            'first_name_en': 'Replacement',
            'last_name_en': 'player',
            'gender': Player.NONE,
            'country': 'RUS',
            'city': None,
            'is_replacement': True,
            'is_hide': False
        }

        self.countries = sorted(self.countries)
        self.cities = sorted(self.cities)

        print('Done. {} players were processed'.format(len(self.players.keys())), end='\n\n')

        # print('Countries:')
        # for country in self.countries:
        #     print(country)
        #
        # print('')
        #
        # print('Cities:')
        # for city in self.cities:
        #     print(city)
        #
        # print('')

        print('Process clubs...')

        with open(clubs_csv, 'r') as f:
            reader = csv.DictReader(f, delimiter=',')

            for row in reader:
                club_id = row['club_id'].strip().lower()
                name = row['name'].strip()
                website = row['website'].strip()
                city = row['city'].strip().lower().title()

                name_ru = name
                name_en = unidecode(name)

                if city and city not in self.cities:
                    print('City is not exists: {}'.format(city))

                if club_id in self.clubs:
                    print('Double for {} club'.format(self.clubs))
                    continue

                self.clubs[club_id] = {
                    'id': club_id,
                    'name_ru': name_ru,
                    'name_en': name_en,
                    'website': website,
                    'city': city,
                }

        print('Done. {} clubs were processed'.format(len(self.clubs.keys())), end='\n\n')

        print('Process tournaments...')

        with open(tournaments_csv, 'r') as f:
            reader = csv.DictReader(f, delimiter=',')

            for row in reader:
                tournament_id = row['tournament_id'].strip().lower()
                club_id = row['club_id'].strip().lower()
                sessions = row['sessions'].strip().lower()
                date = row['date'].strip().lower()
                name = row['name'].strip()
                city = row['city'].strip().lower().title()
                t_type = row['type'].strip().lower()

                name_ru = name
                name_en = unidecode(name)

                sessions = sessions and int(sessions) or 0
                date = datetime.strptime(date, '%m/%d/%Y')

                if city and city not in self.cities:
                    print('City is not exists: {}'.format(city))

                if club_id and club_id not in self.clubs:
                    print('Club with {} id is not exists'.format(club_id))

                if tournament_id in self.tournaments:
                    print('Double for {} tournament'.format(tournament_id))
                    continue

                self.tournaments[tournament_id] = {
                    'id': tournament_id,
                    'club_id': club_id,
                    'name_ru': name_ru,
                    'name_en': name_en,
                    'sessions': sessions,
                    'date': date,
                    'city': city,
                    'type': t_type,
                    'results': []
                }

        print('Done. {} tournaments were processed'.format(len(self.tournaments.keys())), end='\n\n')

        print('Process tournament results...')
        results_counter = 0

        with open(results_csv, 'r') as f:
            reader = csv.DictReader(f, delimiter=',')

            for row in reader:
                tournament_id = row['tournament_id'].strip().lower()
                place = row['place'].strip().lower()
                player_name = row['name'].strip().lower()
                scores = row['scores'].strip().lower()

                scores = scores and float(scores) or 0
                place = int(place)

                if tournament_id not in self.tournaments:
                    print('Wrong tournament id: {}'.format(tournament_id))
                    continue

                if player_name not in self.players:
                    print('Player {} is not exists'.format(player_name))

                self.tournaments[tournament_id]['results'].append({
                    'place': place,
                    'player_name': player_name,
                    'scores': scores,
                })

                results_counter += 1

        print('Done. {} results were processed'.format(results_counter), end='\n\n')

        print('Inserting data into DB...', end='\n\n')

        countries_data = {
            'AUT': {
                'code': 'AT',
                'name_en': 'Austria',
                'name_ru': 'Австрия'
            },
            'BLR': {
                'code': 'BY',
                'name_en': 'Belarus',
                'name_ru': 'Белоруссия'
            },
            'FIN': {
                'code': 'FI',
                'name_en': 'Finland',
                'name_ru': 'Финляндия'
            },
            'GBR': {
                'code': 'GB',
                'name_en': 'United Kingdom',
                'name_ru': 'Великобритания'
            },
            'JPN': {
                'code': 'JP',
                'name_en': 'Japan',
                'name_ru': 'Япония'
            },
            'KAZ': {
                'code': 'KZ',
                'name_en': 'Kazakhstan',
                'name_ru': 'Казахстан'
            },
            'KOR': {
                'code': 'KR',
                'name_en': 'South Korea',
                'name_ru': 'Южная Корея'
            },
            'MDA': {
                'code': 'MD',
                'name_en': 'Moldova',
                'name_ru': 'Молдова'
            },
            'RUS': {
                'code': 'RU',
                'name_en': 'Russia',
                'name_ru': 'Россия'
            },
            'UKR': {
                'code': 'UA',
                'name_en': 'Ukraine',
                'name_ru': 'Украина'
            },
            'UZB': {
                'code': 'UZ',
                'name_en': 'Uzbekistan',
                'name_ru': 'Узбекистан'
            },
        }

        country_objects = {}
        cities_objects = {}
        club_objects = {}
        tournament_objects = {}
        player_objects = {}

        tournament_types = {
            'club': TournamentType.objects.create(name_ru='Клубный', name_en='Club', slug='club'),
            'ema': TournamentType.objects.create(name_ru='EMA', name_en='EMA', slug='ema')
        }

        with transaction.atomic():
            for country in self.countries:
                country_objects[country] = Country.objects.create(**countries_data[country])

            for city in self.cities:
                cities_objects[city] = City.objects.create(name_ru=city, name_en=unidecode(city))

            for club_id in self.clubs:
                club_dict = self.clubs[club_id]
                club_objects[club_id] = Club.objects.create(
                    name_ru=club_dict['name_ru'],
                    name_en=club_dict['name_en'],
                    slug=slugify(club_dict['name_en']),
                    website=club_dict['website'],
                    city=club_dict['city'] and cities_objects[club_dict['city']] or None,
                    country=country_objects['RUS'],
                )

            for player_id in self.players:
                player_dict = self.players[player_id]
                player_dict['country'] = country_objects[player_dict['country']]
                player_dict['city'] = player_dict['city'] and cities_objects[player_dict['city']] or None
                del player_dict['name']

                player_objects[player_id] = Player.objects.create(**player_dict)

            for tournament_id in self.tournaments:
                tournament_dict = self.tournaments[tournament_id]
                tournament_object = Tournament.objects.create(
                    name_en=tournament_dict['name_en'],
                    name_ru=tournament_dict['name_ru'],
                    number_of_sessions=tournament_dict['sessions'],
                    date=tournament_dict['date'],
                    tournament_type=tournament_types[tournament_dict['type']],
                    city=tournament_dict['city'] and cities_objects[tournament_dict['city']] or None,
                    country=country_objects['RUS'],
                )

                if tournament_dict['club_id']:
                    tournament_object.clubs.add(club_objects[tournament_dict['club_id']])

                tournament_objects[tournament_id] = tournament_object

                for tournament_result in tournament_dict['results']:
                    TournamentResult.objects.create(
                        player=player_objects[tournament_result['player_name']],
                        tournament=tournament_object,
                        place=tournament_result['place'],
                        scores=tournament_result['scores'],
                    )

        print('Done')

    def process_player(self, row):
        player_name = row['name'].strip().lower()
        player_name_en = row['name_en'].strip().lower()
        gender = row['gender'].strip().lower()
        country = row['country'].strip().upper()
        city = row['city'].strip().lower().title()

        if player_name in self.players:
            print('Double player: {}'.format(player_name))

        temp = player_name.split(' ')
        last_name_ru = temp[0].strip().title()
        first_name_ru = temp[1].strip().title()

        if player_name_en:
            temp = player_name_en.split(' ')
            first_name_en = temp[0].strip().title()
            last_name_en = temp[1].strip().title()
        else:
            first_name_en = unidecode(first_name_ru).title()
            last_name_en = unidecode(last_name_ru).title()

        if gender == u'ж':
            gender = Player.FEMALE
        elif gender == u'м':
            gender = Player.MALE
        else:
            gender = Player.NONE

        if country not in self.countries:
            self.countries.append(country)

        if city and city not in self.cities:
            self.cities.append(city)

        return {
            'name': player_name,
            'first_name_ru': first_name_ru,
            'last_name_ru': last_name_ru,
            'first_name_en': first_name_en,
            'last_name_en': last_name_en,
            'gender': gender,
            'country': country,
            'city': city,
            'is_replacement': False,
            'is_hide': False
        }
