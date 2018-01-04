from django.shortcuts import render, get_object_or_404

from player.models import Player


def player_details(request, slug):
    player = get_object_or_404(Player, slug=slug)

    rating_results = player.rating_results.all().order_by('id')

    return render(request, 'player/details.html', {
        'player': player,
        'rating_results': rating_results
    })
