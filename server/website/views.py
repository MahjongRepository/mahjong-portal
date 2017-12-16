from django.shortcuts import render

from player.models import Player
from rating.models import Rating


def home(request):
    rating = Rating.objects.get(type=Rating.INNER)
    players = Player.objects.all().order_by('inner_rating_place', 'id')[:25]

    return render(request, 'website/home.html', {
        'page': 'home',
        'players': players,
        'rating': rating
    })


def about(request):
    return render(request, 'website/about.html', {
        'page': 'about'
    })
