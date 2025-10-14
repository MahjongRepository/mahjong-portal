# -*- coding: utf-8 -*-
from urllib.parse import parse_qs, urlparse

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST

from account.forms import LoginForm
from account.models import AttachingPlayerRequest, PantheonInfoUpdateLog, User
from player.models import Player
from player.player_helper import PlayerHelper
from player.tenhou.models import TenhouAggregatedStatistics


def do_login(request):
    form = LoginForm(initial={"next": request.GET.get("next", "/")})
    if request.POST:
        form = LoginForm(request.POST)
        if form.is_valid():
            pantheon_id = form.user_data["person_id"]
            try:
                user = User.objects.get(new_pantheon_id=pantheon_id)
            except User.DoesNotExist:
                user = User.objects.create_user(
                    username=form.user_data["email"],
                    email=form.user_data["email"],
                    password=None,
                )
                user.new_pantheon_id = pantheon_id
                user.save()

            PantheonInfoUpdateLog.objects.create(user=user, pantheon_id=pantheon_id, updated_information=form.user_data)

            login(request, user)

            return redirect(form.cleaned_data["next"])

    return render(request, "account/login.html", {"form": form})


@csrf_protect
def account_settings(request):
    success = None
    error_code = None
    current_player = None
    current_tenhou_account = None
    if request.user is not None and request.user.attached_player is not None:
        current_player = request.user.attached_player
        current_tenhou_account = current_player.tenhou_object

    if request.POST:
        if request.user is not None and request.user.is_authenticated:
            if current_player is not None and current_player.tenhou_object is not None:
                current_tenhou = current_player.tenhou_object
                current_tenhou_nickname = current_tenhou.tenhou_username
                if current_tenhou_nickname is not None:
                    log_url = request.POST.get("log_url")
                    if log_url is not None:
                        error_code, log_hash = get_replay_hash(log_url)
                        if error_code is None and log_hash is not None:
                            stat = TenhouAggregatedStatistics.objects.get(
                                game_players=TenhouAggregatedStatistics.FOUR_PLAYERS, tenhou_object=current_tenhou
                            )
                            if stat is not None:
                                new_rating = PlayerHelper.calculate_rating(
                                    log_hash, current_tenhou_nickname, stat.played_games
                                )
                                if new_rating is not None:
                                    stat.rate = new_rating
                                    stat.save()
                                    success = True
                                else:
                                    success = False
                                    error_code = 2
                            else:
                                success = False
                                error_code = None
                        else:
                            success = False
                    else:
                        success = False
                        error_code = 1

    return render(
        request,
        "account/settings.html",
        {
            "success": success,
            "error_code": error_code,
            "player": current_player,
            "tenhou_account": current_tenhou_account,
        },
    )


def get_replay_hash(log_link):
    # error_message = _("This is not looks like a link to the game log.")
    error_code = 1

    log_link = log_link.replace("https://", "http://")

    log_link = log_link.strip()
    if not log_link.startswith("http://tenhou.net/"):
        return error_code, None

    attributes = parse_qs(urlparse(log_link).query)

    if "log" not in attributes:
        return error_code, None

    log_id = attributes["log"][0]
    return None, log_id


@login_required
@require_POST
def request_player_and_user_connection(request, slug):
    player = get_object_or_404(Player, slug=slug)
    contacts = request.POST.get("contacts")
    if not contacts:
        return redirect("player_details", slug)

    AttachingPlayerRequest.objects.create(user=request.user, player=player, contacts=contacts)
    messages.success(request, _("Request was created."))
    return redirect("player_details", player.slug)
