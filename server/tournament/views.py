from django.shortcuts import render, get_object_or_404

from tournament.models import Tournament, TournamentResult


def tournament_list(request):
    tournaments = Tournament.objects.all().order_by('-date')
    return render(request, 'tournament/list.html', {
        'tournaments': tournaments,
        'page': 'tournament'
    })


def tournament_details(request, tournament_slug):
    tournament = get_object_or_404(Tournament, slug=tournament_slug)
    results = TournamentResult.objects.filter(tournament=tournament).order_by('place')
    return render(request, 'tournament/details.html', {
        'tournament': tournament,
        'results': results,
        'page': 'tournament'
    })
