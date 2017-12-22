from django.db.models import Count
from django.shortcuts import render, get_object_or_404

from club.models import Club


def club_list(request):
    clubs = Club.objects.all().order_by('city__name')

    return render(request, 'club/list.html', {
        'clubs': clubs,
        'page': 'club'
    })


def club_details(request, slug):
    club = get_object_or_404(Club, slug=slug)
    tournaments = club.tournament_set.all().order_by('-date')
    return render(request, 'club/details.html', {
        'club': club,
        'tournaments': tournaments,
        'page': 'club'
    })
