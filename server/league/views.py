from django.shortcuts import get_object_or_404, render

from league.models import League


def league_details(request, slug):
    league = get_object_or_404(League, slug=slug)
    return render(
        request,
        "league/view.html",
        {
            "league": league,
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
    return render(
        request,
        "league/schedule.html",
        {
            "league": league,
        },
    )
