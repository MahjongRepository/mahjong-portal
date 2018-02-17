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

    def add_arguments(self, parser):
        parser.add_argument('--rebuild-from-zero', default=False, type=bool)
        parser.add_argument('--associate-players', default=False, type=bool)
        parser.add_argument('--club-id', type=int, default=None)

    def handle(self, *args, **options):
        print('{0}: Start'.format(get_date_string()))
        
        rebuild_from_zero = options.get('rebuild_from_zero')
        associate_players = options.get('associate_players')
        club_id = options.get('club_id')
        
        if club_id:
            clubs = Club.objects.filter(id=club_id)
        else:
            clubs = Club.objects.exclude(pantheon_ids__isnull=True)
            
        for club in clubs:
            print('Processing: {}'.format(club.name))

            event_ids = club.pantheon_ids.split(',')

            if associate_players:
                # we had to run for the first time
                # to set pantheon ids to users
                self.associate_players(club, event_ids)
            else:
                with transaction.atomic():
                    self.download_game_results(club, event_ids, rebuild_from_zero)
                    self.calculate_club_rating(club, event_ids)
            
        print('{0}: End'.format(get_date_string()))

    def calculate_club_rating(self, club, event_ids):
        print('Calculate club rating')
        
        players = club.players.all()

        ClubRating.objects.filter(club=club).delete()
        
        # let's query all data once
        # ro reduce queries count
        all_session_results = (PantheonSessionResult.objects
                               .filter(session__event_id__in=event_ids)
                               .filter(session__status=PantheonSession.FINISHED))
        all_rounds = (PantheonRound.objects
                      .filter(event__id__in=event_ids)
                      .filter(session__status=PantheonSession.FINISHED))
        
        players_sessions = {}
        for session_result in all_session_results:
            if session_result.player_id not in players_sessions:
                players_sessions[session_result.player_id] = []

            players_sessions[session_result.player_id].append(session_result.session_id)
        
        session_rounds = {}
        for round_item in all_rounds:
            if round_item.session_id not in session_rounds:
                session_rounds[round_item.session_id] = []

            session_rounds[round_item.session_id].append(round_item)

        for player in players:
            base_query = ClubSessionResult.objects.filter(club_session__club=club, player=player)

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
            open_hand = 0
            successful_riichi = 0

            if player and player.pantheon_id:
                player_sessions = players_sessions[player.pantheon_id]
                
                player_rounds = []
                for session_id in player_sessions:
                    player_rounds.extend(session_rounds[session_id])

                total_rounds_count = self._calculate_rounds_count(player_rounds)

                win_rounds = self._get_player_rounds(player_rounds, 'win', player.pantheon_id)
                lose_rounds = self._get_player_rounds(player_rounds, 'lose', player.pantheon_id)
                riichi_rounds = self._get_player_rounds(player_rounds, 'riichi', player.pantheon_id)

                win_rounds_count = len(win_rounds)
                lose_rounds_count = len(lose_rounds)
                riichi_rounds_count = len(riichi_rounds)

                feed_percentage = (lose_rounds_count / total_rounds_count) * 100

                dora_count = sum([x.dora for x in win_rounds if x.dora])
                average_dora_in_hand = dora_count / win_rounds_count

                open_hand = len([x for x in win_rounds if x.open_hand])
                open_hand = (open_hand / win_rounds_count) * 100

                total_yaku = []
                for round_item in win_rounds:
                    total_yaku.extend(round_item.yaku.split(','))

                riichi_count = total_yaku.count('33')
                ippatsu_count = total_yaku.count('35')

                successful_riichi = riichi_rounds_count and (riichi_count / riichi_rounds_count) * 100 or 0

                ippatsu_chance = ippatsu_count and (ippatsu_count / riichi_count) * 100 or 0

            ClubRating.objects.create(
                club=club,
                player=player,
                games_count=games_count,
                average_place=average_place,
                ippatsu_chance=ippatsu_chance,
                average_dora_in_hand=average_dora_in_hand,
                first_place=first_place,
                second_place=second_place,
                third_place=third_place,
                fourth_place=fourth_place,
                feed_percentage=feed_percentage,
                open_hand=open_hand,
                successful_riichi=successful_riichi,
            )

    def _calculate_rounds_count(self, rounds):
        """
        All of these code exists because of multi ron format in pantheon
        """
        total_rounds_count = 0

        counted_multi_ron = {}
        for item in rounds:
            if item.multi_ron:
                key = '{}_{}'.format(item.session_id, item.round)
                # we had to count multi ron only once for our stat
                if key in counted_multi_ron:
                    continue
                else:
                    counted_multi_ron[key] = 1

            total_rounds_count += 1

        return total_rounds_count

    def _get_player_rounds(self, rounds, round_type, player_id):
        results = []

        counted_multi_ron = {}
        for item in rounds:
            if round_type == 'win' and item.winner_id == player_id:
                results.append(item)

            if round_type == 'lose' and item.loser_id == player_id and (item.outcome == PantheonRound.RON or item.outcome == PantheonRound.MULTI_RON):
                results.append(item)

            if round_type == 'riichi' and item.riichi:
                riichi_players = [int(x) for x in item.riichi.split(',')]
                if player_id in riichi_players:
                    results.append(item)

        return results

    def download_game_results(self, club, event_ids, rebuild_from_zero):
        print('Download game results')
        
        sync_data, _ = ClubSessionSyncData.objects.get_or_create(club=club)
        
        if rebuild_from_zero:
            last_session_id = 0
            ClubSessionResult.objects.filter(club_session__club=club).delete()
            ClubSession.objects.filter(club=club).delete()
        else:
            # we had to download only new sessions
            last_session_id = sync_data.last_session_id or 0

        # prepare players
        players = Player.objects.filter(pantheon_id__isnull=False)
        players_dict = {}
        for player in players:
            players_dict[player.pantheon_id] = player
            
        missed_players = {}

        sessions = (PantheonSession.objects
                    .filter(event_id__in=event_ids)
                    .filter(status=PantheonSession.FINISHED)
                    .filter(id__gt=last_session_id)
                    .order_by('id')
                    .prefetch_related('players')
                    .prefetch_related('results'))

        print('Games to add: {}'.format(sessions.count()))

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
                pantheon_id=session.representational_hash,
                pantheon_event_id=session.event_id
            )

            for prepared_result in prepared_results:
                player_string = ''
                player = prepared_result['player_id'] in players_dict and players_dict[prepared_result['player_id']] or None
                if not player:
                    player_string = prepared_result['display_name']
                    # we need to display to the admin
                    missed_players[prepared_result['player_id']] = prepared_result['display_name']

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
        
        for key in missed_players.keys():
            print('Players without pantheon id: {}, {}'.format(
                key,
                missed_players[key]
            ))

    def associate_players(self, club, event_ids):
        print('Associate players')
        
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

            try:
                player = Player.objects.get(first_name_ru=first_name, last_name_ru=last_name)
                player.pantheon_id = pantheon_player.id
                player.save()

                club.players.add(player)
            except Player.DoesNotExist:
                try:
                    player = Player.objects.get(pantheon_id=pantheon_player.id)
                except Player.DoesNotExist:
                    games = PantheonSessionResult.objects.filter(player_id=pantheon_player.id).count()
                    print('Missed player: {} Games: {} ID: {}'.format(pantheon_player.display_name, games, pantheon_player.id))
