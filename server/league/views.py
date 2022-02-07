from django.shortcuts import get_object_or_404, render

from league.models import League, LeagueSession


def league_details(request, slug):
    league = get_object_or_404(League, slug=slug)
    upcoming_session = (
        league.sessions.filter(status=LeagueSession.PLANNED).prefetch_related("games", "games__players").first()
    )
    return render(
        request,
        "league/view.html",
        {
            "league": league,
            "upcoming_session": upcoming_session,
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
    sessions = league.sessions.all().prefetch_related("games", "games__players")
    return render(
        request,
        "league/schedule.html",
        {
            "league": league,
            "sessions": sessions,
        },
    )
