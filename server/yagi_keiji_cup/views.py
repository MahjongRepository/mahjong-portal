# -*- coding: utf-8 -*-
from django.http import Http404
from django.shortcuts import get_object_or_404, render

from yagi_keiji_cup.models import YagiKeijiCupResults, YagiKeijiCupSettings


def cup_final_information(request):

    item_class = YagiKeijiCupSettings
    yagiKejiCupSettings = get_object_or_404(item_class, is_main=True)

    if yagiKejiCupSettings.is_hidden:
        raise Http404

    results = YagiKeijiCupResults.objects.order_by("-team_scores").all()

    return render(
        request,
        "yagi_keiji_cup/yagi_keiji_cup.html",
        {
            "results": results,
        },
    )
