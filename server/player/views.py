from django.shortcuts import render, get_object_or_404

from player.models import Player
from rating.models import RatingDelta
from tournament.models import TournamentResult


def player_details(request, slug):
    player = get_object_or_404(Player, slug=slug)

    rating_results = player.rating_results.all().order_by('rating__order')

    used_tournaments = (RatingDelta.objects
                                   .filter(rating__id__in=[x.rating.id for x in rating_results])
                                   .filter(is_active=True)
                                   .values_list('tournament_id', flat=True)
                                   .distinct())

    other_tournaments = (TournamentResult.objects
                                         .filter(player=player)
                                         .exclude(tournament_id__in=used_tournaments)
                                         .prefetch_related('tournament')
                                         .order_by('-tournament__end_date'))

    return render(request, 'player/details.html', {
        'player': player,
        'rating_results': rating_results,
        'other_tournaments': other_tournaments
    })
