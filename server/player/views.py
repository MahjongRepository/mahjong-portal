from django.shortcuts import render, get_object_or_404

from player.models import Player
from rating.models import RatingDelta


def player_details(request, slug):
    player = get_object_or_404(Player, slug=slug)
    deltas = RatingDelta.objects.filter(player=player).order_by('-tournament__end_date')
    return render(request, 'player/details.html', {
        'player': player,
        'deltas': deltas
    })
