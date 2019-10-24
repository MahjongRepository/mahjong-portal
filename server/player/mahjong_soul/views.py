from django.http import Http404
from django.shortcuts import render

from player.mahjong_soul.models import MSAccountStatistic


def ms_accounts(request, stat_type='four'):
    if stat_type not in ['four', 'three']:
        raise Http404

    four_players = False
    filter_type = MSAccountStatistic.THREE_PLAYERS
    if stat_type == 'four':
        four_players = True
        filter_type = MSAccountStatistic.FOUR_PLAYERS

    statistics = MSAccountStatistic.objects.filter(
        game_type=filter_type,
        rank__isnull=False
    ).select_related('account', 'account__player').order_by('-rank', '-points')

    return render(request, 'ms/ms_accounts.html', {
        'statistics': statistics,
        'four_players': four_players
    })
