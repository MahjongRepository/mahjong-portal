from datetime import datetime, timedelta

import pytz
from django.db.models import F, Sum
from django.http import Http404
from django.shortcuts import render
from django.utils import timezone

from player.tenhou.models import (
    TenhouNickname,
    CollectedYakuman,
    TenhouGameLog,
    TenhouAggregatedStatistics,
)
from utils.tenhou.current_tenhou_games import get_latest_wg_games


def get_current_tenhou_games(request):
    return render(request, "tenhou/tenhou_games.html", {})


def get_current_tenhou_games_async(request):
    games = get_latest_wg_games()

    tenhou_objects = TenhouNickname.objects.all().prefetch_related("player")
    player_profiles = {}
    for tenhou_object in tenhou_objects:
        player_profiles[tenhou_object.tenhou_username] = tenhou_object.player

    # let's find players from our database that are playing right now
    found_players = []
    our_players_games = {}

    high_level_games = {}
    high_level_sanma_games = {}

    bot_games = {}

    for game in games:
        for player in game["players"]:
            # we found a player from our database
            if player["name"] in player_profiles:
                found_players.append(player)
                our_players_games[game["game_id"]] = game

            if player["name"].startswith(u"ⓝ"):
                player["is_bot"] = True
                bot_games[game["game_id"]] = game

            if player["dan"] >= 18:
                if len(game["players"]) == 3:
                    high_level_sanma_games[game["game_id"]] = game
                else:
                    high_level_games[game["game_id"]] = game

    return render(
        request,
        "tenhou/tenhou_games_async.html",
        {
            "our_players_games": our_players_games.values(),
            "high_level_games": high_level_games.values(),
            "high_level_hirosima_games": high_level_sanma_games.values(),
            "bot_games": bot_games.values(),
            "player_profiles": player_profiles,
        },
    )


def latest_yakumans(request):
    yakumans = (
        CollectedYakuman.objects.all()
        .order_by("-date")
        .prefetch_related("tenhou_object", "tenhou_object__player")
    )
    return render(request, "tenhou/latest_yakumans.html", {"yakumans": yakumans})


def tenhou_accounts(request):
    accounts = (
        TenhouAggregatedStatistics.objects.filter(
            game_players=TenhouAggregatedStatistics.FOUR_PLAYERS
        )
        .filter(tenhou_object__is_active=True)
        .order_by("-rank", "-rate", "-pt")
        .prefetch_related("tenhou_object")
        .prefetch_related("tenhou_object__player")
        .prefetch_related("tenhou_object__player__city")
    )
    return render(request, "tenhou/tenhou_accounts.html", {"accounts": accounts})


def games_history(request, year=None, month=None, day=None):
    query_date = timezone.now().date()
    if year and month and day:
        try:
            query_date = datetime(
                year=int(year), month=int(month), day=int(day), tzinfo=pytz.utc
            )
        except ValueError:
            raise Http404

    previous_day = query_date - timedelta(days=1)

    games = (
        TenhouGameLog.objects.filter(game_date__date=query_date)
        .filter(game_players=TenhouGameLog.FOUR_PLAYERS)
        .prefetch_related("tenhou_object")
        .prefetch_related("tenhou_object__player")
        .order_by("-game_date")
    )

    rank_changes = TenhouGameLog.objects.filter(
        game_date__date=query_date, game_players=TenhouGameLog.FOUR_PLAYERS
    ).exclude(rank=F("next_rank"))

    return render(
        request,
        "tenhou/games_history.html",
        {
            "query_date": query_date,
            "previous_day": previous_day,
            "games": games,
            "total": games.count(),
            "time_spent": (games.aggregate(Sum("game_length"))["game_length__sum"] or 0)
            / 60.0,
            "rank_changes": rank_changes,
        },
    )
