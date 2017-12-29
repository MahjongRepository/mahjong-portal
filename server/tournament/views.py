from django.shortcuts import render, get_object_or_404

from settings.models import TournamentType
from tournament.models import Tournament, TournamentResult


def tournament_list(request, year=None):

    default_year_filter = 'all'
    try:
        current_year = year or default_year_filter
        if current_year != default_year_filter:
            current_year = int(current_year)
    except ValueError:
        current_year = default_year_filter

    years = [2017, 2016, 2015, 2014, 2013]

    if current_year != default_year_filter and current_year not in years:
        current_year = default_year_filter

    tournaments = (Tournament.objects
                             .filter(is_upcoming=False)
                             .exclude(tournament_type__slug=TournamentType.FOREIGN_EMA)
                             .order_by('-end_date'))
    upcoming_tournaments = Tournament.objects.filter(is_upcoming=True).order_by('start_date')

    if current_year != default_year_filter:
        tournaments = tournaments.filter(end_date__year=current_year)

    return render(request, 'tournament/list.html', {
        'tournaments': tournaments,
        'upcoming_tournaments': upcoming_tournaments,
        'years': years,
        'current_year': current_year,
        'page': 'tournament',
    })


def tournament_details(request, slug):
    tournament = get_object_or_404(Tournament, slug=slug)
    results = TournamentResult.objects.filter(tournament=tournament).order_by('place')

    return render(request, 'tournament/details.html', {
        'tournament': tournament,
        'results': results,
        'page': 'tournament'
    })
