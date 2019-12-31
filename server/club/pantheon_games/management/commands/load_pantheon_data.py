from datetime import timedelta

import pytz
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from club.club_games.models import ClubSession, ClubSessionResult, ClubRating, ClubSessionSyncData
from club.models import Club
from club.pantheon_games.models import PantheonSession, PantheonSessionResult, PantheonRound
from player.models import Player
from player.tenhou.models import TenhouAggregatedStatistics


def get_date_string():
    return timezone.now().strftime('%H:%M:%S')


class Command(BaseCommand):
    NUMBER_OF_CLUB_STATISTICS_DAYS = 180

    def add_arguments(self, parser):
        parser.add_argument('--rebuild-from-zero', default=False, type=bool)
        parser.add_argument('--club-id', type=int, default=None)

    def handle(self, *args, **options):
        print('{0}: Start'.format(get_date_string()))

        rebuild_from_zero = options.get('rebuild_from_zero')
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

            with transaction.atomic():
                self.download_game_results(club, event_ids, rebuild_from_zero)
                self.calculate_club_rating(club, event_ids)

        print('')
        print('{0}: End'.format(get_date_string()))

    def download_game_results(self, club, event_ids, rebuild_from_zero):
        print('')
        print('Downloading game results...')

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
            date = session.end_date.replace(tzinfo=pytz.timezone('CET'))
            club_session = ClubSession.objects.create(
                club=club,
                date=date,
                pantheon_id=session.representational_hash,
                pantheon_event_id=session.event_id
            )

            for prepared_result in prepared_results:
                player_string = ''
                player = prepared_result['player_id'] in players_dict and players_dict[
                    prepared_result['player_id']] or None
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

        print('Downloading completed')

    def calculate_club_rating(self, club, event_ids):
        print('')
        print('Calculating club rating...')

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

        days_ago = timezone.now() - timedelta(days=self.NUMBER_OF_CLUB_STATISTICS_DAYS)
        for player in players:
            base_query = (ClubSessionResult
                          .objects
                          .filter(club_session__club=club, player=player)
                          .filter(club_session__date__gte=days_ago))

            games_count = base_query.count()

            # skip players without games
            if not games_count:
                continue

            first_place = base_query.filter(place=1).count()
            second_place = base_query.filter(place=2).count()
            third_place = base_query.filter(place=3).count()
            fourth_place = base_query.filter(place=4).count()

            average_place = (first_place + second_place * 2 + third_place * 3 + fourth_place * 4) / games_count

            first_place = (first_place / games_count) * 100
            second_place = (second_place / games_count) * 100
            third_place = (third_place / games_count) * 100
            fourth_place = (fourth_place / games_count) * 100

            if player and player.pantheon_id:
                player_sessions = players_sessions[player.pantheon_id]

                player_rounds = []
                for session_id in player_sessions:
                    player_rounds.extend(session_rounds[session_id])

            stat = (TenhouAggregatedStatistics.objects
                    .filter(tenhou_object__player=player)
                    .filter(game_players=TenhouAggregatedStatistics.FOUR_PLAYERS)
                    .last())

            ClubRating.objects.create(
                club=club,
                player=player,
                games_count=games_count,
                average_place=average_place,
                first_place=first_place,
                second_place=second_place,
                third_place=third_place,
                fourth_place=fourth_place,
                rank=stat and stat.rank or None
            )

        print('Calculating completed')
