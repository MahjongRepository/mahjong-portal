# -*- coding: utf-8 -*-

import csv
import io

from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify

from player.models import Player
from settings.models import Country
from system.ema_players_admin.forms import AddPlayerForm


@login_required
@user_passes_test(lambda u: u.is_ema_players_manager)
def list_of_ema_players(request):
    query = request.GET.get("q")
    players = _get_players_query(query)
    return render(request, "ema_players_admin/players_list.html", {"players": players, "query": query})


@login_required
@user_passes_test(lambda u: u.is_ema_players_manager)
def download_players_list_csv(request):
    query = request.GET.get("q")
    players = _get_players_query(query)

    content = io.StringIO()
    writer = csv.writer(content)
    writer.writerow(["EMA_NUMBER", "LAST_NAME", "FIRST_NAME", "COUNTRY"])
    for player in players:
        writer.writerow([player.ema_id, player.last_name_en.upper(), player.first_name_en.upper(), "RUS : Russia"])

    response = HttpResponse(content.getvalue(), content_type="text/x-csv")
    response["Content-Disposition"] = "attachment; filename=ema_players.csv"
    return response


def _get_players_query(query=None):
    players = Player.ema_queryset()

    if query:
        players = players.filter(
            Q(first_name_ru__icontains=query)
            | Q(last_name_ru__icontains=query)
            | Q(first_name_en__icontains=query)
            | Q(last_name_en__icontains=query)
            | Q(ema_id__icontains=query)
        )
    return players


@login_required
@user_passes_test(lambda u: u.is_ema_players_manager)
def add_new_player(request):
    form = AddPlayerForm()
    if request.POST:
        form = AddPlayerForm(request.POST)
        if form.is_valid():
            player = form.save(commit=False)
            player.country = Country.objects.get(code="RU")
            player.ema_id = player.latest_ema_id + 1
            player.slug = slugify("{} {}".format(player.last_name_en, player.first_name_en))
            player.save()

            return redirect("list_of_ema_players")

    return render(request, "ema_players_admin/add_player.html", {"form": form})


@login_required
@user_passes_test(lambda u: u.is_ema_players_manager)
def assign_ema_id(request, player_id):
    player = get_object_or_404(Player, id=player_id)
    player.ema_id = player.latest_ema_id + 1
    player.save()
    return redirect("list_of_ema_players")
