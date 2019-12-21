from collections import defaultdict

from django.db.models import F
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone

from club.club_games.models import ClubRating
from player.models import Player
from player.tenhou.models import TenhouNickname
from rating.models import RatingDelta, Rating, RatingResult, TournamentCoefficients
from rating.utils import get_latest_rating_date, parse_rating_date
from tournament.models import TournamentResult


def player_by_id_details(request, player_id):
    player = get_object_or_404(Player, id=player_id)
    return redirect(player_details, player.slug)


def player_by_id_tenhou_details(request, player_id):
    player = get_object_or_404(Player, id=player_id)
    return redirect(player_tenhou_details, player.slug)


def player_details(request, slug, year=None, month=None, day=None):
    player = get_object_or_404(Player, slug=slug)

    _, entered_date, _ = parse_rating_date(year, month, day)

    ratings = Rating.objects.all().order_by('order')
    rating_results = []
    for rating in ratings:
        if not entered_date:
            _, rating_date = get_latest_rating_date(rating)
        else:
            rating_date = entered_date

        result = RatingResult.objects.filter(date=rating_date, rating=rating, player=player).first()
        if result:
            rating_results.append(result)

    tournament_results = (TournamentResult.objects
                          .filter(player=player)
                          .prefetch_related('tournament')
                          .order_by('-tournament__end_date'))[:10]

    tenhou_data = TenhouNickname.objects.filter(player=player, is_main=True)
    club_ratings = (ClubRating.objects
                    .filter(player=player)
                    .prefetch_related('club', 'club__city')
                    .order_by('-games_count'))

    return render(request, 'player/details.html', {
        'player': player,
        'rating_results': rating_results,
        'tournament_results': tournament_results,
        'tenhou_data': tenhou_data,
        'club_ratings': club_ratings,
        'rating_date': entered_date
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


def player_rating_details(request, slug, rating_slug, year=None, month=None, day=None):
    player = get_object_or_404(Player, slug=slug)
    rating = get_object_or_404(Rating, slug=rating_slug)

    today, rating_date, is_last = parse_rating_date(year, month, day)
    if not rating_date:
        today, rating_date = get_latest_rating_date(rating)

    rating_result = get_object_or_404(RatingResult, rating=rating, player=player, date=rating_date)

    rating_deltas = (RatingDelta.objects
                     .filter(player=player, rating=rating, date=rating_date)
                     .prefetch_related('player')
                     .prefetch_related('tournament')
                     .order_by('-tournament__end_date'))

    top_tournaments_number = 3 if rating.is_online() else 4
    top_tournament_ids = tuple(d.tournament_id for d in sorted(
        rating_deltas,
        reverse=True,
        key=lambda d: float(d.base_rank) * float(d.coefficient_obj.age) * float(d.coefficient_value)
    ))[:top_tournaments_number]

    last_rating_place = RatingResult.objects.filter(rating=rating, date=rating_date).order_by('place').last().place
    filtered_results = _get_rating_changes(rating, player, today)

    return render(request, 'player/rating_details.html', {
        'player': player,
        'rating': rating,
        'rating_deltas': rating_deltas,
        'rating_result': rating_result,
        'filtered_results': filtered_results,
        'last_rating_place': last_rating_place,
        'top_tournament_ids': top_tournament_ids,
        'rating_date': rating_date,
        'today': today,
    })


def player_rating_changes(request, slug, rating_slug, year=None, month=None, day=None):
    player = get_object_or_404(Player, slug=slug)
    rating = get_object_or_404(Rating, slug=rating_slug)

    today, rating_date, is_last = parse_rating_date(year, month, day)
    if not rating_date:
        today, rating_date = get_latest_rating_date(rating)

    rating_result = get_object_or_404(RatingResult, rating=rating, player=player, date=rating_date)
    filtered_results = reversed(_get_rating_changes(rating, player, today))

    return render(request, 'player/rating_changes.html', {
        'player': player,
        'rating': rating,
        'results': filtered_results,
        'rating_date': rating_date,
        'today': today,
        'rating_result': rating_result,
    })


def _get_rating_changes(rating, player, today):
    tournament_coefficients = TournamentCoefficients.objects.filter(
        tournament__results__player=player,
        rating=rating,
    ).exclude(
        previous_age=None,
    ).exclude(
        age=F('previous_age'),
    ).order_by(
        'date'
    ).select_related(
        'tournament'
    )
    tournament_coefficients_by_date = defaultdict(list)
    for tc in tournament_coefficients:
        tournament_coefficients_by_date[tc.date].append({
            'tournament_name': tc.tournament.name,
            'age': float(tc.age),
            'previous_age': float(tc.previous_age)
        })

    all_rating_results = RatingResult.objects.filter(
        rating=rating, player=player
    ).filter(date__lte=today).order_by('date')

    filtered_results = []
    previous_score = -1
    previous_place = -1
    for x in all_rating_results:
        if x.score != previous_score or x.place != previous_place:
            filtered_results.append({
                'result': x,
                'previous_score': previous_score,
                'previous_place': previous_place,
                'coefficients': tournament_coefficients_by_date.get(x.date)
            })
        previous_score = x.score
        previous_place = x.place

    return filtered_results


def player_tenhou_details(request, slug):
    player = get_object_or_404(Player, slug=slug)
    tenhou_data = TenhouNickname.objects.filter(
        player=player
    ).order_by('-is_main').prefetch_related('aggregated_statistics')
    return render(request, 'player/tenhou.html', {
        'player': player,
        'tenhou_data': tenhou_data,
    })
