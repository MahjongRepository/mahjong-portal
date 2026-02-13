# -*- coding: utf-8 -*-
from django.http import Http404
from django.shortcuts import get_object_or_404, render

from tournament.models import Tournament
from yagi_keiji_cup.models import YagiKeijiCupResults, YagiKeijiCupSettings


def cup_final_information(request):

    item_class = YagiKeijiCupSettings
    yagiKejiCupSettings = get_object_or_404(item_class, is_main=True)

    if yagiKejiCupSettings.is_hidden:
        raise Http404

    main_tournament = Tournament.objects.get(slug="yagi-keiji-cup")
    tenhou_tournament = Tournament.objects.get(slug="yagi-keiji-cup-tenhou")
    majsoul_tournament = Tournament.objects.get(slug="yagi-keiji-cup-majsoul")

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
    team_place = 1
    last_team_scores_tuple = ()
    for result in results:
        best_team_avg_place = min(result.tenhou_player_avg_place, result.majsoul_player_avg_place)
        current_team_place = team_place
        if len(last_team_scores_tuple) > 0:
            if last_team_scores_tuple[0] == result.team_scores and last_team_scores_tuple[1] == best_team_avg_place:
                current_team_place = last_team_scores_tuple[2]

        calculated_results.append(
            {
                "result": result,
                "team_avg_place": best_team_avg_place,
                "team_place": current_team_place,
            }
        )
        last_team_scores_tuple = (result.team_scores, best_team_avg_place, current_team_place)
        team_place = team_place + 1

    return render(
        request,
        "yagi_keiji_cup/yagi_keiji_cup.html",
        {
            "results": calculated_results,
            "main_tournament": main_tournament,
            "tenhou_tournament": tenhou_tournament,
            "majsoul_tournament": majsoul_tournament,
        },
    )
