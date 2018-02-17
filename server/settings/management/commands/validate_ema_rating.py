import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from django.template.defaultfilters import floatformat

from rating.models import RatingResult, Rating


class Command(BaseCommand):

    def handle(self, *args, **options):
        url = 'http://mahjong-europe.org/ranking/rcr.html'

        page = requests.get(url)
        soup = BeautifulSoup(page.content, 'html.parser', from_encoding='utf-8')

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

            key = '{}{}'.format(last_name, first_name)
            ema_players[key] = {
                'place': place,
                'last_name': last_name,
                'first_name': first_name,
                'scores': scores,
                'ema_id': ema_id,
            }

        players = {}
        for result in RatingResult.objects.filter(rating__type=Rating.EMA):
            key = '{}{}'.format(result.player.last_name_en, result.player.first_name_en)
            players[key] = {
                'place': result.place,
                'last_name': result.player.last_name_en,
                'first_name': result.player.first_name_en,
                # round didn't work as ema for 0.5 scores
                'scores': int(floatformat(result.score, 0)),
                'ema_id': result.player.ema_id,
            }

        missed = []
        for key in ema_players.keys():
            ema_player = ema_players[key]

            if key in players:
                player = players[key]
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
            else:
                missed.append(ema_player)

        print('')
        for player in missed:
            print('Missed player in our rating: {}'.format(format_player(player)))

        print('')
        for key in players.keys():
            if key not in ema_players:
                player = players[key]
                print('User had to be removed from rating: {}'.format(format_player(player)))


def format_player(player):
    return '{} {} {}'.format(player['ema_id'], player['last_name'], player['first_name'])
