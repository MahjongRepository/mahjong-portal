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

            ema_players[ema_id] = {
                'place': place,
                'last_name': last_name,
                'first_name': first_name,
                'scores': scores,
                'ema_id': ema_id,
            }

        players = {}
        for result in RatingResult.objects.filter(rating__type=Rating.EMA, is_last=True):
            players[result.player.ema_id] = {
                'place': result.place,
                'last_name': result.player.last_name_en,
                'first_name': result.player.first_name_en,
                # round didn't work as ema for 0.5 scores
                'scores': int(floatformat(result.score, 0)),
                'ema_id': result.player.ema_id,
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

                if player['first_name'] != ema_player['first_name'] or player['last_name'] != ema_player['last_name']:
                    print('Not identical names: our={} ema={}'.format(
                        format_player(player),
                        format_player(ema_player)
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


def format_player(player):
    return '{} {} {}'.format(player['ema_id'], player['last_name'], player['first_name'])
