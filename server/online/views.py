# -*- coding: utf-8 -*-

from functools import wraps

import requests
import ujson as json
from django.conf import settings
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from online.handler import TournamentHandler
from online.management.portal_autobot import PortalAutoBot
from online.models import TournamentPlayers
from tournament.models import Tournament
from utils.general import make_random_letters_and_digit_string
from utils.pantheon import add_user_to_pantheon

# todo: remove global tournament auto bot object for support multiple tournament
bot = PortalAutoBot()


@user_passes_test(lambda u: u.is_superuser)
@login_required
def add_user_to_the_pantheon(request, record_id):
    record = TournamentPlayers.objects.get(id=record_id)
    add_user_to_pantheon(record)
    referer = request.META.get("HTTP_REFERER")
    # TODO temporary remove untrusted redirect from user referer
    referer = "/"
    return redirect(referer)


@user_passes_test(lambda u: u.is_superuser)
@login_required
def disable_user_in_pantheon(request, record_id):
    record = TournamentPlayers.objects.get(id=record_id)

    headers = {"X-Auth-Token": settings.PANTHEON_ADMIN_TOKEN}

    data = {
        "jsonrpc": "2.0",
        "method": "updatePlayerSeatingFlagCP",
        "params": {
            "playerId": record.pantheon_id,
            "eventId": settings.PANTHEON_TOURNAMENT_EVENT_ID,
            "ignoreSeating": 1,
        },
        "id": make_random_letters_and_digit_string(),
    }

    response = requests.post(settings.PANTHEON_OLD_API_URL, json=data, headers=headers)
    if response.status_code == 500:
        return HttpResponse("Disable player. 500 response")

    content = response.json()
    if content.get("error"):
        return HttpResponse("Disable player. Pantheon error: {}".format(content.get("error")))

    record.enabled_in_pantheon = False
    record.save()

    referer = request.META.get("HTTP_REFERER")
    # TODO temporary remove untrusted redirect from user referer
    referer = "/"
    return redirect(referer)


@user_passes_test(lambda u: u.is_superuser)
@login_required
def toggle_replacement_flag_in_pantheon(request, record_id):
    record = TournamentPlayers.objects.get(id=record_id)

    headers = {"X-Auth-Token": settings.PANTHEON_ADMIN_TOKEN}

    new_is_replacement = not record.is_replacement

    data = {
        "jsonrpc": "2.0",
        "method": "updatePlayer",
        "params": {
            "id": record.pantheon_id,
            "ident": "",
            "alias": "",
            "displayName": "",
            "tenhouId": record.tenhou_username,
            "isReplacement": new_is_replacement,
        },
        "id": make_random_letters_and_digit_string(),
    }

    response = requests.post(settings.PANTHEON_OLD_API_URL, json=data, headers=headers)
    if response.status_code == 500:
        return HttpResponse("updatePlayer. 500 response")

    content = response.json()
    if content.get("error"):
        return HttpResponse("updatePlayer. Pantheon error: {}".format(content.get("error")))

    record.is_replacement = new_is_replacement
    record.save()

    referer = request.META.get("HTTP_REFERER")
    # TODO temporary remove untrusted redirect from user referer
    referer = "/"
    return redirect(referer)


@require_POST
def finish_game_api(request):
    api_token = request.POST.get("api_token")
    if api_token != settings.TOURNAMENT_API_TOKEN:
        return HttpResponse(status=403)

    message = request.POST.get("message")

    handler = TournamentHandler()
    handler.init(tournament=Tournament.objects.get(id=settings.TOURNAMENT_ID), lobby="", game_type="", destination="")
    handler.game_pre_end(message)

    return JsonResponse({"success": True})


def autobot_token_require(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        request_data = json.loads(request.body)
        api_token = request_data.get("api_token")
        if not api_token or api_token != settings.AUTO_BOT_TOKEN:
            return HttpResponse(status=403)

        return function(request, *args, **kwargs)

    return wrap


def tournament_data_require(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        request_data = json.loads(request.body)
        tournament_id = request_data.get("tournament_id")
        if not tournament_id:
            return HttpResponse(status=400)

        lobby_id = request_data.get("lobby_id")
        if not lobby_id:
            return HttpResponse(status=400)

        bot.init(int(tournament_id), int(lobby_id))
        return function(request, *args, **kwargs)

    return wrap


@require_POST
@csrf_exempt
@autobot_token_require
@tournament_data_require
def open_registration(request):
    bot.open_registration(None)
    return JsonResponse({"success": True})


@require_POST
@csrf_exempt
@autobot_token_require
@tournament_data_require
def close_registration(request):
    bot.close_registration(None)
    return JsonResponse({"success": True})


@require_POST
@csrf_exempt
@autobot_token_require
@tournament_data_require
def check_new_notifications(request):
    request_data = json.loads(request.body)
    tournament_id = request_data.get("tournament_id")
    if not tournament_id:
        return JsonResponse({"notifications": []})
    notifications = bot.check_new_notifications(tournament_id)
    return JsonResponse({"notifications": notifications})


@require_POST
@csrf_exempt
@autobot_token_require
@tournament_data_require
def process_notification(request):
    request_data = json.loads(request.body)

    notification_id = request_data.get("notification_id")
    if not notification_id:
        return HttpResponse(status=400)

    tournament_id = request_data["tournament_id"]
    bot.process_notification(notification_id, tournament_id)
    return JsonResponse({"success": True})


@require_POST
@csrf_exempt
@autobot_token_require
@tournament_data_require
def prepare_next_round(request):
    response = bot.prepare_next_round()
    return JsonResponse(response)


@require_POST
@csrf_exempt
@autobot_token_require
@tournament_data_require
def confirm_player(request):
    request_data = json.loads(request.body)

    nickname = request_data.get("nickname")
    if not nickname:
        return HttpResponse(status=400)

    telegram_username = request_data.get("telegram_username")
    discord_username = request_data.get("discord_username")

    requested_lang = request_data.get("lang")
    # todo: fix default ru locale
    if not requested_lang:
        requested_lang = "ru"

    confirm_message = bot.confirm_player(nickname, telegram_username, discord_username, requested_lang)
    return JsonResponse({"message": confirm_message})


@require_POST
@csrf_exempt
@autobot_token_require
@tournament_data_require
def create_start_game_notification(request):
    request_data = json.loads(request.body)

    tour = request_data.get("tour")
    if not tour:
        return HttpResponse(status=400)

    table_number = request_data.get("table_number")
    if not table_number:
        return HttpResponse(status=400)

    notification_type = request_data.get("type")
    if not notification_type:
        return HttpResponse(status=400)

    missed_players = request_data.get("missed_players")
    if not missed_players:
        missed_players = []

    # todo: handle message?
    bot.create_start_game_notification(tour, table_number, notification_type, missed_players)
    return JsonResponse({"success": True})


@require_POST
@csrf_exempt
@autobot_token_require
@tournament_data_require
def game_finish(request):
    request_data = json.loads(request.body)

    log_id = request_data.get("log_id")
    if not log_id:
        return HttpResponse(status=400)

    players = request_data.get("players")
    if not players:
        return HttpResponse(status=400)

    log_content = request_data.get("log_content")
    if not log_content:
        return HttpResponse(status=400)

    log_time = request_data.get("log_time")
    if not log_time:
        return HttpResponse(status=400)

    confirm_message = bot.game_finish(log_id, players, log_content, log_time)
    return JsonResponse({"message": confirm_message[0], "is_error": confirm_message[1]})


@require_POST
@csrf_exempt
@autobot_token_require
@tournament_data_require
def admin_confirm_player(request):
    request_data = json.loads(request.body)

    nickname = request_data.get("nickname")
    if not nickname:
        return HttpResponse(status=400)

    friend_id = request_data.get("friend_id")
    if not friend_id:
        return HttpResponse(status=400)

    telegram_username = request_data.get("telegram_username")
    if not telegram_username:
        return HttpResponse(status=400)

    confirm_message = bot.admin_confirm_player(friend_id, nickname, telegram_username)
    return JsonResponse({"message": confirm_message})


@require_POST
@csrf_exempt
@autobot_token_require
@tournament_data_require
def get_tournament_status(request):
    request_data = json.loads(request.body)
    requested_lang = request_data.get("lang")
    # todo: fix default ru locale
    if not requested_lang:
        requested_lang = "ru"

    message = bot.get_tournament_status(requested_lang)
    return JsonResponse({"message": message})


@require_POST
@csrf_exempt
@autobot_token_require
@tournament_data_require
def get_allowed_players(request):
    players = bot.get_allowed_players()
    return JsonResponse({"players": players})


@require_POST
@csrf_exempt
@autobot_token_require
@tournament_data_require
def add_game_log(request):
    request_data = json.loads(request.body)

    log_link = request_data.get("log_link")
    if not log_link:
        return HttpResponse(status=400)

    confirm_message = bot.add_game_log(log_link)
    return JsonResponse({"message": confirm_message[0], "is_error": confirm_message[1]})


@require_POST
@csrf_exempt
@autobot_token_require
@tournament_data_require
def add_penalty_game(request):
    request_data = json.loads(request.body)

    game_id = request_data.get("game_id")
    if not game_id:
        return HttpResponse(status=400)

    message = bot.add_penalty_game(game_id)
    return JsonResponse({"message": message})


@require_POST
@csrf_exempt
@autobot_token_require
@tournament_data_require
def send_team_names_to_pantheon(request):
    message = bot.send_team_names_to_pantheon()
    return JsonResponse({"message": message})
