# -*- coding: utf-8 -*-
from django.http import Http404
from django.shortcuts import get_object_or_404, render

from yagi_keiji_cup.models import YagiKeijiCupResults, YagiKeijiCupSettings


def cup_final_information(request):

    item_class = YagiKeijiCupSettings
    yagiKejiCupSettings = get_object_or_404(item_class, is_main=True)

    if yagiKejiCupSettings.is_hidden:
        raise Http404

    results = YagiKeijiCupResults.objects.all()
    results = sorted(
        results,
        key=lambda x: (
            -x.team_scores,
            -(x.tenhou_player_game_count + x.majsoul_player_game_count),
            min(x.tenhou_player_avg_place, x.majsoul_player_avg_place),
        ),
    )

    calculated_results = []
    for result in results:
        calculated_results.append(
            {"result": result, "team_avg_place": min(result.tenhou_player_avg_place, result.majsoul_player_avg_place)}
        )

    return render(
        request,
        "yagi_keiji_cup/yagi_keiji_cup.html",
        {
            "results": calculated_results,
        },
    )
