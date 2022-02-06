from django.shortcuts import get_object_or_404, render

from league.models import League, LeagueSession, LeagueTeam


def league_details(request, slug):
    league = get_object_or_404(League, slug=slug)
    upcoming_session = (
        league.sessions.filter(status=LeagueSession.PLANNED).prefetch_related("games", "games__players").first()
    )
    all_teams = LeagueTeam.objects.all()
    playing_team_ids = []
    for game in upcoming_session.games.all():
        for player in game.players.all():
            if player.team_id not in playing_team_ids:
                playing_team_ids.append(player.team_id)

    missing_teams_for_session = [x for x in all_teams if x.id not in playing_team_ids]

    return render(
        request,
        "league/view.html",
        {
            "league": league,
            "upcoming_session": upcoming_session,
            "missing_teams_for_session": missing_teams_for_session,
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
