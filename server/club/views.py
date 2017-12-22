from django.db.models import Count
from django.shortcuts import render, get_object_or_404
from django.utils.translation import get_language

from club.models import Club


def club_list(request):
    clubs = Club.objects.all().order_by('city__name')

    map_language = 'en_US'
    if get_language() == 'ru':
        map_language = 'ru_RU'

    return render(request, 'club/list.html', {
        'clubs': clubs,
        'map_language': map_language,
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
