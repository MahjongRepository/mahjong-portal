from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse

from player.models import Player
from player.tenhou.models import TenhouNickname
from rating.models import RatingDelta, Rating, RatingResult
from tournament.models import TournamentResult


def player_by_id_details(request, player_id):
    player = get_object_or_404(Player, id=player_id)
    return redirect(player_details, player.slug)


def player_by_id_tenhou_details(request, player_id):
    player = get_object_or_404(Player, id=player_id)
    return redirect(player_tenhou_details, player.slug)


def player_details(request, slug):
    player = get_object_or_404(Player, slug=slug)

    rating_results = player.rating_results.filter(is_last=True).order_by('rating__order')
    tournament_results = (TournamentResult.objects
                          .filter(player=player)
                          .prefetch_related('tournament')
                          .order_by('-tournament__end_date'))[:10]

    tenhou_data = TenhouNickname.objects.filter(player=player, is_main=True)

    return render(request, 'player/details.html', {
        'player': player,
        'rating_results': rating_results,
        'tournament_results': tournament_results,
        'tenhou_data': tenhou_data
    })


def player_tournaments(request, slug):
    player = get_object_or_404(Player, slug=slug)

    tournament_results = (TournamentResult.objects
                          .filter(player=player)
                          .prefetch_related('tournament')
                          .order_by('-tournament__end_date'))

    return render(request, 'player/tournaments.html', {
        'player': player,
        'tournament_results': tournament_results
    })


def player_rating_details(request, slug, rating_slug):
    player = get_object_or_404(Player, slug=slug)
    rating = get_object_or_404(Rating, slug=rating_slug)

    rating_result = get_object_or_404(RatingResult, rating=rating, player=player, is_last=True)
    all_rating_results = RatingResult.objects.filter(rating=rating, player=player).order_by('date')
    filtered_results = []

    previous_score = -1
    previous_place = -1
    for x in all_rating_results:
        need_to_add = False

        if x.score != previous_score:
            need_to_add = True
            previous_score = x.score

        if x.place != previous_place:
            need_to_add = True
            previous_place = x.place

        if need_to_add:
            filtered_results.append(x)

    rating_deltas = (RatingDelta.objects
                     .filter(player=player, rating=rating, is_last=True)
                     .prefetch_related('player')
                     .prefetch_related('tournament')
                     .order_by('-tournament__end_date'))

    last_rating_place = RatingResult.objects.filter(rating=rating, is_last=True).order_by('place').last().place

    return render(request, 'player/rating_details.html', {
        'player': player,
        'rating': rating,
        'rating_deltas': rating_deltas,
        'rating_result': rating_result,
        'filtered_results': filtered_results,
        'last_rating_place': last_rating_place
    })


def player_tenhou_details(request, slug):
    player = get_object_or_404(Player, slug=slug)
    tenhou_data = TenhouNickname.objects.filter(player=player).order_by('-is_main')
    return render(request, 'player/tenhou.html', {
        'player': player,
        'tenhou_data': tenhou_data,
    })
