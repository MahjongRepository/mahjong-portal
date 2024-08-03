# -*- coding: utf-8 -*-

from datetime import timedelta

from django.db.models import Q
from django.http import Http404
from django.shortcuts import render
from django.utils import timezone

from player.mahjong_soul.models import MSAccountStatistic


def ms_accounts(request, stat_type="four"):
    if stat_type not in ["four", "three"]:
        raise Http404

    four_players = False
    current_game_type = MSAccountStatistic.FOUR_PLAYERS
    if stat_type == "four":
        four_players = True
    else:
        current_game_type = MSAccountStatistic.THREE_PLAYERS

    statistics = (
        MSAccountStatistic.objects.filter(rank__isnull=False, game_type=current_game_type)
        .exclude(account__account_name="")
        .filter(Q(tonpusen_games__gt=0) | Q(hanchan_games__gt=0))
        .order_by("-rank", "-points")
        .prefetch_related("account", "account__player")
    )

    # hide accounts from the list that didn't play long time
    filtered_statistics = []
    current_time = timezone.now() - timedelta(days=180)
    for statistic in statistics:
        last_played_date = statistic.last_account_played_date
        if last_played_date <= current_time:
            continue

        filtered_statistics.append({"stat": statistic, "last_played_date": last_played_date})

    return render(request, "ms/ms_accounts.html", {"statistics": filtered_statistics, "four_players": four_players})
