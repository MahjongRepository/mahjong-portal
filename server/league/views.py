from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from league.models import League, LeagueGameSlot, LeaguePlayer, LeagueSession


def league_details(request, slug):
    league = get_object_or_404(League, slug=slug)
    upcoming_session = (
        league.sessions.filter(status=LeagueSession.PLANNED).prefetch_related("games", "games__slots").first()
    )
    upcoming_session_games = upcoming_session.games.all()
    my_team_games = []
    user_team_id = None
    if request.user.is_authenticated:
        try:
            player = LeaguePlayer.objects.get(user=request.user)
            user_team_id = player.team_id
            for game in upcoming_session_games:
                for game_slot in game.slots.all():
                    if game_slot.team_id == player.team_id:
                        my_team_games.append(game)
            upcoming_session_games = [x for x in upcoming_session_games if x.id not in [y.id for y in my_team_games]]
        except LeaguePlayer.DoesNotExist:
            pass
    upcoming_session._custom_games = upcoming_session_games

    return render(
        request,
        "league/view.html",
        {
            "league": league,
            "upcoming_session": upcoming_session,
            "my_team_games": my_team_games,
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
    sessions = league.sessions.all().prefetch_related("games", "games__slots")
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
    slot = get_object_or_404(LeagueGameSlot, id=slot_id)
    player = get_object_or_404(LeaguePlayer, user=request.user)
    if slot.team_id != player.team_id:
        raise Http404
    slot.assigned_player = player
    slot.save()
    return redirect(request.META.get("HTTP_REFERER"))
