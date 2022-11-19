from random import shuffle
from urllib.parse import unquote

import requests
from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.timezone import now

from league.models import League, LeagueGame, LeagueGameSlot, LeaguePlayer, LeagueSession


def league_details(request, slug):
    league = get_object_or_404(League, slug=slug)
    upcoming_sessions = league.sessions.filter(status=LeagueSession.PLANNED).prefetch_related("games", "games__slots")

    user_team_id = None
    for upcoming_session in upcoming_sessions:
        upcoming_session_games = upcoming_session.games.all()

        my_team_games = []
        if request.user.is_authenticated:
            try:
                player = LeaguePlayer.objects.get(user=request.user, team__league=league)
                user_team_id = player.team_id
                for game in upcoming_session_games:
                    for game_slot in game.slots.all():
                        if game_slot.team_id == player.team_id:
                            my_team_games.append(game)
                upcoming_session_games = [
                    x for x in upcoming_session_games if x.id not in [y.id for y in my_team_games]
                ]
            except LeaguePlayer.DoesNotExist:
                pass

        upcoming_session.custom_games = upcoming_session_games
        upcoming_session.my_team_games = my_team_games
        start_in_minutes = (upcoming_session.start_time - now()).total_seconds() / 60
        upcoming_session.show_assigned_players_for_all = start_in_minutes <= 60

    return render(
        request,
        "league/view.html",
        {
            "league": league,
            "upcoming_sessions": upcoming_sessions,
            "user_team_id": user_team_id,
        },
    )


def league_teams(request, slug):
    league = get_object_or_404(League, slug=slug)
    return render(
        request,
        "league/teams.html",
        {
            "league": league,
        },
    )


def league_schedule(request, slug):
    league = get_object_or_404(League, slug=slug)
    sessions = league.sessions.exclude(status=LeagueSession.FINISHED).prefetch_related("games", "games__slots")
    return render(
        request,
        "league/schedule.html",
        {
            "league": league,
            "sessions": sessions,
        },
    )


@login_required
def league_confirm_slot(request, slot_id):
    # TODO don't use hardcoded league
    league = League.objects.get(slug="yoroshiku-league-2")
    slot = get_object_or_404(LeagueGameSlot, id=slot_id)
    player = get_object_or_404(LeaguePlayer, user=request.user, team__league=league)
    if slot.team_id != player.team_id:
        raise Http404
    slot.assigned_player = player
    slot.save()
    return redirect(request.META.get("HTTP_REFERER"))


@login_required
@permission_required("league.start_league_game")
def start_game(request, game_id):
    game = LeagueGame.objects.get(id=game_id)
    slots = game.slots.all()

    player_names = [x.assigned_player.tenhou_nickname for x in slots]
    shuffle(player_names)

    url = "https://tenhou.net/cs/edit/cmd_start.cgi"
    data = {
        "L": settings.LEAGUE_PRIVATE_TENHOU_LOBBY,
        "R2": settings.LEAGUE_GAME_TYPE,
        "RND": "default",
        "WG": 1,
        "M": "\r\n".join([x for x in player_names]),
    }

    headers = {
        "Origin": "http://tenhou.net",
        "Content-Type": "application/x-www-form-urlencoded",
        "Referer": "http://tenhou.net/cs/edit/?{}".format(settings.LEAGUE_PRIVATE_TENHOU_LOBBY),
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0"
    }

    response = requests.post(url, data=data, headers=headers, allow_redirects=False)
    result = unquote(response.content.decode("utf-8"))
    if result.startswith("FAILED") or result.startswith("MEMBER NOT FOUND"):
        HttpResponse(result)
    else:
        game.status = LeagueGame.STARTED
        game.save()

    return HttpResponse(result)
