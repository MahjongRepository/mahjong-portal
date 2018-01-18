import csv
from datetime import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify

from player.models import Player
from settings.models import Country, City, TournamentType
from tournament.models import Tournament, TournamentResult


def get_date_string():
    return timezone.now().strftime('%H:%M:%S')


class Command(BaseCommand):
    tournaments_file = 'tournaments.csv'
    results_file = 'results.csv'

    def add_arguments(self, parser):
        parser.add_argument('csv_path', type=str)
        parser.add_argument('tournament_id', type=int)
        parser.add_argument('--create_results', type=bool, default=False)

    def handle(self, *args, **options):
        print('{0}: Start'.format(get_date_string()))

        with open(options['csv_path'], 'r') as f:
            reader = csv.DictReader(f, delimiter=',')

            missed_countries = []
            missed_players = []

            tournament = Tournament.objects.get(id=options['tournament_id'])
            TournamentResult.objects.filter(tournament=tournament).delete()

            for row in reader:
                country = row['country'].strip().upper()
                ema_id = row['ema_id'].strip()
                place = row['place'].strip()
                first_name = row['first_name'].strip()
                last_name = row['last_name'].strip()
                scores = int(row['scores'].strip())

                if country and country not in missed_countries:
                    try:
                        Country.objects.get(code=country)
                    except Country.DoesNotExist:
                        missed_countries.append(country)

                player = None

                if 'player' in first_name.lower() or 'player' in last_name.lower():
                    player = Player.all_objects.get(is_replacement=True)

                if ema_id:
                    try:
                        player = Player.objects.get(ema_id=ema_id)
                    except Player.DoesNotExist:
                        pass

                if not player:
                    try:
                        player = Player.objects.get(last_name_en=last_name, first_name_en=first_name)
                    except Player.DoesNotExist:
                        pass

                if not player:
                    missed_players.append([last_name, first_name, country, ema_id])

                if options['create_results']:
                    if not player:
                        country = Country.objects.get(code=country)

                        player = Player.objects.create(
                            first_name_ru=first_name,
                            first_name_en=first_name,
                            last_name_ru=last_name,
                            last_name_en=last_name,
                            country=country,
                            slug=slugify('{} {}'.format(last_name, first_name))
                        )

                    TournamentResult.objects.create(
                        tournament=tournament,
                        player=player,
                        place=place,
                        scores=scores
                    )

            if missed_countries:
                print('Missed countries:')
                for item in missed_countries:
                    print(item)

            if missed_players:
                print('Missed players:')
                for item in missed_players:
                    print(item)

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
                tournament_type=Tournament.FOREIGN_EMA,
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
