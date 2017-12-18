from django.shortcuts import render
from haystack.forms import ModelSearchForm

from player.models import Player
from rating.models import Rating


def home(request):
    rating = Rating.objects.get(type=Rating.INNER)
    players = Player.objects.all().order_by('inner_rating_place')[:25]

    return render(request, 'website/home.html', {
        'page': 'home',
        'players': players,
        'rating': rating
    })


def about(request):
    return render(request, 'website/about.html', {
        'page': 'about'
    })


def search(request):
    query = request.GET.get('q', '')

    search_form = ModelSearchForm(request.GET, load_all=True)
    results = search_form.search()

    query_list = [x.object for x in results]
    players = [x for x in query_list if x.__class__ == Player]

    players = sorted(players, key=lambda x: x.inner_rating_place)

    return render(request, 'website/search.html', {
        'players': players,
        'search_query': query
    })
