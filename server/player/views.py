from django.shortcuts import render, get_object_or_404, redirect

from player.models import Player
from rating.models import RatingDelta, Rating, RatingResult
from tournament.models import TournamentResult


def player_by_id_details(request, player_id):
    player = get_object_or_404(Player, id=player_id)
    return redirect(player_details, player.slug)


def player_details(request, slug):
    player = get_object_or_404(Player, slug=slug)

    rating_results = player.rating_results.all().order_by('rating__order')
    tournament_results = []

    # let's display player tournament if ratings result is empty
    # for example player participated in only one tournament
    if not rating_results.count():
        tournament_results = RatingDelta.objects.filter(player=player)

    return render(request, 'player/details.html', {
        'player': player,
        'rating_results': rating_results,
        'tournament_results': tournament_results
    })


def player_rating_details(request, slug, rating_slug):
    player = get_object_or_404(Player, slug=slug)
    rating = get_object_or_404(Rating, slug=rating_slug)

    rating_result = get_object_or_404(RatingResult, rating=rating, player=player)

    rating_deltas = (RatingDelta.objects
                      .filter(player=player, rating=rating)
                      .prefetch_related('player')
                      .prefetch_related('tournament')
                      .order_by('-tournament__end_date'))

    return render(request, 'player/rating_details.html', {
        'player': player,
        'rating': rating,
        'rating_deltas': rating_deltas,
        'rating_result': rating_result
    })
