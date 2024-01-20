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
from online.models import TournamentGame, TournamentNotification, TournamentPlayers
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
    return redirect(request.META.get("HTTP_REFERER"))


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

    return redirect(request.META.get("HTTP_REFERER"))


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

    return redirect(request.META.get("HTTP_REFERER"))


@user_passes_test(lambda u: u.is_superuser)
@login_required
def add_penalty_game(request, game_id):
    game = TournamentGame.objects.get(id=game_id)

    headers = {"X-Auth-Token": settings.PANTHEON_ADMIN_TOKEN}
    data = {
        "jsonrpc": "2.0",
        "method": "addPenaltyGame",
        "params": {
            "eventId": settings.PANTHEON_TOURNAMENT_EVENT_ID,
            "players": [x.player.pantheon_id for x in game.game_players.all()],
        },
        "id": make_random_letters_and_digit_string(),
    }

    response = requests.post(settings.PANTHEON_OLD_API_URL, json=data, headers=headers)
    if response.status_code == 500:
        return HttpResponse("addPenaltyGame. 500 response")

    content = response.json()
    if content.get("error"):
        return HttpResponse("addPenaltyGame. Pantheon error: {}".format(content.get("error")))

    handler = TournamentHandler()
    handler.init(tournament=Tournament.objects.get(id=settings.TOURNAMENT_ID), lobby="", game_type="", destination="")
    player_names = handler.get_players_message_string([x.player for x in game.game_players.all()])
    handler.create_notification(TournamentNotification.GAME_PENALTY, {"player_names": player_names})
    handler.check_round_was_finished()

    return redirect(request.META.get("HTTP_REFERER"))


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
        api_token = request_data["api_token"]
        if not api_token or api_token != settings.AUTO_BOT_TOKEN:
            return HttpResponse(status=403)

        return function(request, *args, **kwargs)

    return wrap


def tournament_data_require(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        request_data = json.loads(request.body)
        tournament_id = request_data["tournament_id"]
        if not tournament_id:
            return HttpResponse(status=400)

        lobby_id = request_data["lobby_id"]
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
def check_new_notifications(request):
    request_data = json.loads(request.body)
    tournament_id = request_data["tournament_id"]
    notification = bot.check_new_notifications(tournament_id)
    if notification:
        return JsonResponse({"notifications": [notification]})
    return JsonResponse({"notifications": []})


@require_POST
@csrf_exempt
@autobot_token_require
@tournament_data_require
def process_notification(request):
    request_data = json.loads(request.body)

    notification_id = request_data["notification_id"]
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

    nickname = request_data["nickname"]
    if not nickname:
        return HttpResponse(status=400)

    telegram_username = request_data["telegram_username"]
    if not telegram_username:
        return HttpResponse(status=400)

    confirm_message = bot.confirm_player(nickname, telegram_username)
    return JsonResponse({"message": confirm_message})


@require_POST
@csrf_exempt
@autobot_token_require
@tournament_data_require
def create_start_ms_game_notification(request):
    request_data = json.loads(request.body)

    tour = request_data["tour"]
    if not tour:
        return HttpResponse(status=400)

    table_number = request_data["table_number"]
    if not table_number:
        return HttpResponse(status=400)

    notification_type = request_data["type"]
    if not notification_type:
        return HttpResponse(status=400)

    # todo: handle message?
    bot.create_start_ms_game_notification(tour, table_number, notification_type)
    return JsonResponse({"success": True})


@require_POST
@csrf_exempt
@autobot_token_require
@tournament_data_require
def game_finish(request):
    request_data = json.loads(request.body)

    log_id = request_data["log_id"]
    if not log_id:
        return HttpResponse(status=400)

    players = request_data["players"]
    if not players:
        return HttpResponse(status=400)

    log_content = request_data["log_content"]
    if not log_content:
        return HttpResponse(status=400)

    log_time = request_data["log_time"]
    if not log_time:
        return HttpResponse(status=400)

    confirm_message = bot.game_finish(log_id, players, log_content, log_time)
    return JsonResponse({"message": confirm_message})
