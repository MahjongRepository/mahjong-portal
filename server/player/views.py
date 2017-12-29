from django.shortcuts import render, get_object_or_404

from player.models import Player
from rating.models import RatingDelta, Rating, RatingResult


def player_details(request, slug):
    player = get_object_or_404(Player, slug=slug)

    rating = Rating.objects.get(type=Rating.INNER)

    try:
        rating_result = RatingResult.objects.get(player=player, rating=rating)
        deltas = RatingDelta.objects.filter(player=player, rating=rating).order_by('-tournament__end_date')
    except RatingResult.DoesNotExist:
        rating_result = None
        deltas = []

    return render(request, 'player/details.html', {
        'player': player,
        'deltas': deltas,
        'rating_result': rating_result
    })
