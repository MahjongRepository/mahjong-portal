from django.shortcuts import render, get_object_or_404

from tournament.models import Tournament, TournamentResult


def tournament_list(request):
    default_year_filter = 'all'
    try:
        current_year = request.GET.get('year', default_year_filter)
        if current_year != default_year_filter:
            current_year = int(current_year)
    except ValueError:
        current_year = default_year_filter

    years = [2017, 2016, 2015, 2014, 2013]

    if current_year != default_year_filter and current_year not in years:
        current_year = default_year_filter

    tournaments = Tournament.objects.all().order_by('-date')

    if current_year != default_year_filter:
        tournaments = tournaments.filter(date__year=current_year)

    return render(request, 'tournament/list.html', {
        'tournaments': tournaments,
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
