import requests
from django.conf import settings
from django.contrib.auth.decorators import user_passes_test, login_required
from django.http import HttpResponse
from django.shortcuts import redirect

from online.models import TournamentPlayers
from utils.general import make_random_letters_and_digit_string
from utils.pantheon import add_user_to_pantheon


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

    # The first step is update player tenhou nickname
    data = {
        "jsonrpc": "2.0",
        "method": "updatePlayerSeatingFlagCP",
        "params": {"playerId": record.pantheon_id, "eventId": settings.PANTHEON_EVENT_ID, "ignoreSeating": 1},
        "id": make_random_letters_and_digit_string(),
    }

    response = requests.post(settings.PANTHEON_URL, json=data, headers=headers)
    if response.status_code == 500:
        return HttpResponse("Disable player. 500 response")

    content = response.json()
    if content.get("error"):
        return HttpResponse("Disable player. Pantheon error: {}".format(content.get("error")))

    record.enabled_in_pantheon = False
    record.save()

    return redirect(request.META.get("HTTP_REFERER"))
