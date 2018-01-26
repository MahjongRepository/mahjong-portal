from django.shortcuts import render, get_object_or_404
from django.utils.translation import get_language

from club.club_games.models import ClubSession
from club.models import Club


def club_list(request):
    clubs = Club.objects.all().order_by('city__name').prefetch_related('city')

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
    tournaments = club.tournament_set.all().order_by('-end_date')

    club_sessions = club.club_sessions.all().order_by('-date')[:10]

    default_sort = 'avg'
    sort = request.GET.get('sort', default_sort)
    sorting = {
        'avg': 'average_place',
        'games': '-games_count',
        'ippatsu': '-ippatsu_chance',
        'dora': '-average_dora_in_hand',
    }
    sort = sorting.get(sort, default_sort)

    club_rating = club.rating.filter(games_count__gte=5).order_by(sort)

    return render(request, 'club/details.html', {
        'club': club,
        'tournaments': tournaments,
        'page': 'club',
        'club_sessions': club_sessions,
        'club_rating': club_rating
    })
