from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, get_object_or_404

from player.models import Player
from rating.models import Rating


def rating_list(request, rating_slug):
    rating = get_object_or_404(Rating, slug=rating_slug)
    players = Player.objects.all().order_by('inner_rating_place', 'id')

    page = request.GET.get('page')
    paginator = Paginator(players, 25)

    try:
        players = paginator.page(page)
    except PageNotAnInteger:
        players = paginator.page(1)
    except EmptyPage:
        players = paginator.page(paginator.num_pages)

    return render(request, 'rating/list.html', {
        'rating': rating,
        'players': players,
    })
