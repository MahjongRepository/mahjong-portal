import pytz
from django.core.management.base import BaseCommand
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

    def handle(self, *args, **options):
        print('{0}: Start'.format(get_date_string()))

        pantheon_event_ids = [33, 45, 61]
        club_id = 20

        club = Club.objects.get(id=club_id)
        # club.timezone = 'Asia/Irkutsk'
        # club.save()

        # self.associate_players(club, pantheon_event_ids)
        # self.download_game_results(club, pantheon_event_ids)
        self.calculate_club_rating(club, pantheon_event_ids)

        print('{0}: End'.format(get_date_string()))

    def calculate_club_rating(self, club, event_ids):
        players = club.players.all()
        players_strings = (ClubSessionResult.objects
                           .filter(club_session__club=club)
                           .values_list('player_string', flat=True)
                           .distinct())

        players_strings = list(set([x for x in players_strings if x]))

        players = list(players) + players_strings

        ClubRating.objects.filter(club=club).delete()

        for player in players:
            if type(player) == Player:
                player_string = ''
            else:
                player_string = player
                player = None

            if player:
                base_query = ClubSessionResult.objects.filter(club_session__club=club, player=player)
            else:
                base_query = ClubSessionResult.objects.filter(club_session__club=club, player_string=player_string)

            games_count = base_query.count()

            first_place = base_query.filter(place=1).count()
            second_place = base_query.filter(place=2).count()
            third_place = base_query.filter(place=3).count()
            fourth_place = base_query.filter(place=4).count()

            average_place = (first_place + second_place * 2 + third_place * 3 + fourth_place * 4) / games_count

            first_place = (first_place / games_count) * 100
            second_place = (second_place / games_count) * 100
            third_place = (third_place / games_count) * 100
            fourth_place = (fourth_place / games_count) * 100

            ippatsu_chance = 0
            average_dora_in_hand = 0
            feed_percentage = 0

            if player and player.pantheon_id:
                total_rounds = (PantheonRound.objects
                                      .filter(event__id__in=event_ids)
                                      .filter(session__players__player_id=player.pantheon_id))

                total_rounds_count = self._calculate_rounds_count(total_rounds)

                win_rounds = PantheonRound.objects.filter(winner=player.pantheon_id, event__id__in=event_ids)

                lose_rounds = PantheonRound.objects.filter(loser=player.pantheon_id,
                                                           event__id__in=event_ids,
                                                           outcome=PantheonRound.RON)
                lose_rounds_count = self._calculate_rounds_count(lose_rounds)

                feed_percentage = (lose_rounds_count / total_rounds_count) * 100

                dora_count = win_rounds.aggregate(Sum('dora'))['dora__sum']
                rounds_count = win_rounds.count()
                average_dora_in_hand = dora_count / rounds_count

                total_yaku = []
                for round_item in win_rounds:
                    total_yaku.extend(round_item.yaku.split(','))

                riichi_count = total_yaku.count('33')
                ippatsu_count = total_yaku.count('35')

                ippatsu_chance = ippatsu_count and (ippatsu_count / riichi_count) * 100 or 0

            ClubRating.objects.create(
                club=club,
                player=player,
                player_string=player_string,
                games_count=games_count,
                average_place=average_place,
                ippatsu_chance=ippatsu_chance,
                average_dora_in_hand=average_dora_in_hand,
                first_place=first_place,
                second_place=second_place,
                third_place=third_place,
                fourth_place=fourth_place,
                feed_percentage=feed_percentage,
            )

    def _calculate_rounds_count(self, rounds):
        """
        All of this because of multi ron format in pantheon
        """
        total_rounds_count = 0

        counted_multi_ron = {}
        for item in rounds:
            if item.multi_ron:
                key = '{}_{}'.format(item.session_id, item.round)
                # we had to count multi ron only once for our start
                if key in counted_multi_ron:
                    continue
                else:
                    counted_multi_ron[key] = 1

            total_rounds_count += 1

        return total_rounds_count

    def download_game_results(self, club, event_ids):
        ClubSessionResult.objects.all().delete()
        ClubSession.objects.all().delete()

        sync_data, _ = ClubSessionSyncData.objects.get_or_create(club=club)

        # prepare players
        players = Player.objects.filter(pantheon_id__isnull=False)
        players_dict = {}
        for player in players:
            players_dict[player.pantheon_id] = player

        events = PantheonEvent.objects.filter(id__in=event_ids)
        for event in events:
            sessions = (PantheonSession.objects
                        .filter(event=event, status=PantheonSession.FINISHED)
                        .prefetch_related('players')
                        .prefetch_related('results'))

            for session in sessions:
                results = session.results.all()

                prepared_results = {}
                for item in results:
                    prepared_results[item.player_id] = {
                        'score': item.score,
                        'place': item.place,
                        'player_id': item.player_id,
                        'display_name': item.player.display_name,
                    }

                for item in session.players.all():
                    prepared_results[item.player_id]['order'] = item.order

                prepared_results = [x[1] for x in prepared_results.items()]

                club_session = ClubSession.objects.create(
                    club=club,
                    date=make_aware(session.end_date, pytz.timezone('CET')),
                    pantheon_id=session.representational_hash
                )

                for prepared_result in prepared_results:
                    player_string = ''
                    player = prepared_result['player_id'] in players_dict and players_dict[prepared_result['player_id']] or None
                    if not player:
                        player_string = prepared_result['display_name']

                    ClubSessionResult.objects.create(
                        club_session=club_session,
                        player=player,
                        player_string=player_string,
                        place=prepared_result['place'],
                        score=prepared_result['score'],
                        order=prepared_result['order'],
                    )

        session = (PantheonSession.objects
                   .filter(event__id__in=event_ids, status=PantheonSession.FINISHED)
                   .order_by('id')).last()

        sync_data.last_session_id = session.id
        sync_data.save()

    def associate_players(self, club, event_ids):
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
            first_name = temp[1].title()

            if first_name == 'Петр':
                first_name = 'Пётр'

            try:
                player = Player.objects.get(first_name_ru=first_name, last_name_ru=last_name)
                player.pantheon_id = pantheon_player.id
                player.save()

                club.players.add(player)
            except Player.DoesNotExist:
                print(pantheon_player.display_name)
