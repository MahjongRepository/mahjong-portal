import logging

import requests
from django.conf import settings
from django.http import HttpResponse

from online.models import TournamentPlayers
from utils.general import make_random_letters_and_digit_string

logger = logging.getLogger()


def add_user_to_pantheon(record: TournamentPlayers):
    if not record.pantheon_id:
        return

    headers = {"X-Auth-Token": settings.PANTHEON_ADMIN_TOKEN}

    # The first step is update player tenhou nickname
    data = {
        "jsonrpc": "2.0",
        "method": "updatePlayer",
        "params": {
            "id": record.pantheon_id,
            "ident": "",
            "alias": "",
            "displayName": "",
            "tenhouId": record.tenhou_username,
        },
        "id": make_random_letters_and_digit_string(),
    }

    response = requests.post(settings.PANTHEON_URL, json=data, headers=headers)
    if response.status_code == 500:
        return HttpResponse("Update player. 500 response")

    content = response.json()
    if content.get("error"):
        return HttpResponse("Update player. Pantheon error: {}".format(content.get("error")))

    # The second step is enroll player
    data = {
        "jsonrpc": "2.0",
        "method": "enrollPlayerCP",
        "params": {"eventId": settings.PANTHEON_EVENT_ID, "playerId": record.pantheon_id},
        "id": make_random_letters_and_digit_string(),
    }

    response = requests.post(settings.PANTHEON_URL, json=data, headers=headers)
    if response.status_code == 500:
        return HttpResponse("Enroll player. 500 response")

    content = response.json()
    if content.get("error"):
        return HttpResponse("Enroll player. Pantheon error: {}".format(content.get("error")))

    # The third step is register player
    data = {
        "jsonrpc": "2.0",
        "method": "registerPlayerCP",
        "params": {"eventId": settings.PANTHEON_EVENT_ID, "playerId": record.pantheon_id},
        "id": make_random_letters_and_digit_string(),
    }

    response = requests.post(settings.PANTHEON_URL, json=data, headers=headers)
    if response.status_code == 500:
        return HttpResponse("Register player. 500 response")

    content = response.json()
    if content.get("error"):
        return HttpResponse("Register player. Pantheon error: {}".format(content.get("error")))

    record.added_to_pantheon = True
    record.save()


def get_pantheon_swiss_sortition():
    data = {
        "jsonrpc": "2.0",
        "method": "generateSwissSeating",
        "params": {"eventId": settings.PANTHEON_EVENT_ID},
        "id": make_random_letters_and_digit_string(),
    }

    headers = {"X-Auth-Token": settings.PANTHEON_ADMIN_TOKEN}

    response = requests.post(settings.PANTHEON_URL, json=data, headers=headers)
    if response.status_code == 500:
        logger.error("Make sortition. Pantheon 500.")
        return []

    content = response.json()
    if content.get("error"):
        logger.error("Make sortition. Pantheon error. {}".format(content.get("error")))
        return []

    return content["result"]


def add_tenhou_game_to_pantheon(log_link: str):
    data = {
        "jsonrpc": "2.0",
        "method": "addOnlineReplay",
        "params": {"eventId": settings.PANTHEON_EVENT_ID, "link": log_link},
        "id": make_random_letters_and_digit_string(),
    }
    return requests.post(settings.PANTHEON_URL, json=data)
