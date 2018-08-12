import pytz
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from django.utils.timezone import make_aware

from club.club_games.models import ClubSession, ClubSessionResult, ClubRating, ClubSessionSyncData
from club.pantheon_games.models import PantheonEvent, PantheonSession, PantheonSessionResult, PantheonPlayer, \
    PantheonRound
from club.models import Club
from player.models import Player


def get_date_string():
    return timezone.now().strftime('%H:%M:%S')


class Command(BaseCommand):
    # We had to run this command
    # to set pantheon ids to users

    def add_arguments(self, parser):
        parser.add_argument('--club-id', type=int, default=None)

    def handle(self, *args, **options):
        print('{0}: Start'.format(get_date_string()))

        club_id = options.get('club_id')

        if club_id:
            clubs = Club.objects.filter(id=club_id)
        else:
            clubs = Club.objects.exclude(pantheon_ids__isnull=True)

        for club in clubs:
            event_ids = club.pantheon_ids.split(',')
            print('')
            print('Processing: id={}, {}'.format(club.id, club.name))
            print('Events: {}'.format(event_ids))

            self._associate_players(club, event_ids)

        print('')
        print('{0}: End'.format(get_date_string()))

    def _associate_players(self, club, event_ids):
        print('Associating players...')

        club.players.clear()

        player_ids = []
        events = PantheonEvent.objects.filter(id__in=event_ids)
        for event in events:
            sessions = PantheonSession.objects.filter(event=event, status=PantheonSession.FINISHED)

            for session in sessions:
                player_ids.extend([x.player_id for x in session.players.all()])

        player_ids = list(set(player_ids))
        players = PantheonPlayer.objects.filter(id__in=player_ids)

        # set pantheon ids
        for pantheon_player in players:
            temp = pantheon_player.display_name.split(' ')
            last_name = temp[0].title()
            first_name = len(temp) > 1 and temp[1].title() or ''

            try:
                player = Player.objects.get(first_name_ru=first_name, last_name_ru=last_name)
                player.pantheon_id = pantheon_player.id
                player.save()

                club.players.add(player)
            except Player.DoesNotExist:
                try:
                    Player.objects.get(pantheon_id=pantheon_player.id)
                except Player.DoesNotExist:
                    games = PantheonSessionResult.objects.filter(player_id=pantheon_player.id).count()
                    if games > 5:
                        print('Missed player: id={}, {}, Games: {} '.format(
                            pantheon_player.id,
                            pantheon_player.display_name,
                            games
                        ))

        print('Associating completed')
