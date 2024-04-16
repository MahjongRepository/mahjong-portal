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
    statistics = MSAccountStatistic.objects.filter(rank__isnull=False).exclude(account__account_name="")
    if stat_type == "four":
        four_players = True
        statistics = statistics.filter(game_type=MSAccountStatistic.FOUR_PLAYERS)
    else:
        statistics = statistics.filter(game_type=MSAccountStatistic.THREE_PLAYERS)

    statistics = statistics.filter(Q(tonpusen_games__gt=0) | Q(hanchan_games__gt=0))
    statistics = statistics.select_related("account", "account__player").order_by("-rank", "-points")

    # hide accounts from the list that didn't play long time
    filtered_statistics = []
    for statistic in statistics:
        if statistic.last_account_played_date <= timezone.now() - timedelta(days=180):
            continue

        filtered_statistics.append(statistic)

    return render(request, "ms/ms_accounts.html", {"statistics": filtered_statistics, "four_players": four_players})
