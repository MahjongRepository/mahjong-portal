from datetime import datetime, timedelta

import pytz
from django.shortcuts import render
from django.utils import timezone
from django.utils.translation import get_language

from player.tenhou.models import TenhouNickname, CollectedYakuman, TenhouGameLog
from utils.tenhou.current_tenhou_games import get_latest_wg_games


def get_current_tenhou_games(request):
    return render(request, 'tenhou/tenhou_games.html', {})


def get_current_tenhou_games_async(request):
    games = get_latest_wg_games()

    tenhou_objects = TenhouNickname.objects.all().prefetch_related('player')
    player_profiles = {}
    for tenhou_object in tenhou_objects:
        player_profiles[tenhou_object.tenhou_username] = tenhou_object.player

    # let's find players from our database that are playing right now
    found_players = []
    our_players_games = {}

    high_level_games = {}
    high_level_hirosima_games = {}

    for game in games:
        for player in game['players']:
            # we found a player from our database
            if player['name'] in player_profiles:
                found_players.append(player)
                our_players_games[game['game_id']] = game

            if player['dan'] >= 18:
                if len(game['players']) == 3:
                    high_level_hirosima_games[game['game_id']] = game
                else:
                    high_level_games[game['game_id']] = game

    return render(request, 'tenhou/tenhou_games_async.html', {
        'our_players_games': our_players_games.values(),
        'high_level_games': high_level_games.values(),
        'high_level_hirosima_games': high_level_hirosima_games.values(),
        'player_profiles': player_profiles
    })


def latest_yakumans(request):
    yakumans = (CollectedYakuman.objects
                .all()
                .order_by('-date')
                .prefetch_related('tenhou_object', 'tenhou_object__player'))
    return render(request, 'tenhou/latest_yakumans.html', {
        'yakumans': yakumans
    })


def tenhou_accounts(request):
    accounts = (TenhouNickname.objects
                .all()
                .order_by('-rank', '-four_games_rate')
                .prefetch_related('player')
                .prefetch_related('player__city'))
    return render(request, 'tenhou/tenhou_accounts.html', {
        'accounts': accounts
    })


def games_history(request):
    language = get_language()
    date_format = language == 'ru' and '%d.%m.%Y' or '%d.%m.%Y'

    three_days_ago = timezone.now() - timedelta(days=2)
    three_days_ago = datetime(
        three_days_ago.year,
        three_days_ago.month,
        three_days_ago.day,
        tzinfo=pytz.utc
    )

    games_dict = {}
    games = (TenhouGameLog.objects
             .filter(game_date__gte=three_days_ago)
             .prefetch_related('tenhou_object')
             .prefetch_related('tenhou_object__player')
             .order_by('-game_date'))
    for game in games:
        key = game.game_date.strftime(date_format)
        if not games_dict.get(key):
            games_dict[key] = {
                'games': [],
                'total': 0,
                'points': 0,
                'time_spent': 0
            }

        games_dict[key]['games'].append(game)
        games_dict[key]['total'] += 1
        games_dict[key]['points'] += game.delta
        games_dict[key]['time_spent'] += float(game.game_length) / 60.0

    return render(request, 'tenhou/games_history.html', {
        'games': games_dict
    })
