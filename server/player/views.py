# -*- coding: utf-8 -*-

from collections import defaultdict

from django.db.models import F
from django.shortcuts import get_object_or_404, redirect, render
from django.db.models import Avg, Count, Case, When, FloatField
from club.club_games.models import ClubRating
from player.mahjong_soul.models import MSAccount
from player.models import Player
from player.tenhou.models import TenhouAggregatedStatistics, TenhouNickname
from rating.models import ExternalRating, ExternalRatingDelta, Rating, RatingDelta, RatingResult, TournamentCoefficients
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

    ratings = Rating.objects.all().order_by("order")
    rating_results = []
    for rating in ratings:
        if not entered_date:
            _, rating_date = get_latest_rating_date(rating)
        else:
            rating_date = entered_date

        result = RatingResult.objects.filter(date=rating_date, rating=rating, player=player).first()
        if result:
            rating_results.append(result)

    external_ratings = ExternalRating.objects.filter(is_hidden=False).all().order_by("order")
    external_rating_results = []
    _, external_entered_date, _ = parse_rating_date(year, month, day)
    for external_rating in external_ratings:
        if not external_entered_date:
            _, external_rating_date = get_latest_rating_date(external_rating, is_external=True)
        else:
            external_rating_date = external_entered_date

        external_result = ExternalRatingDelta.objects.filter(
            date=external_rating_date, rating=external_rating, player=player
        ).first()
        if external_result:
            external_rating_results.append(external_result)

    tournament_results = (
        TournamentResult.objects.filter(player=player).prefetch_related("tournament").order_by("-tournament__end_date")
    )[:10]

    tenhou_data = TenhouNickname.all_objects.filter(player=player, is_main=True)
    ms_data = MSAccount.objects.filter(player=player).first()
    club_ratings = (
        ClubRating.objects.filter(player=player).prefetch_related("club", "club__city").order_by("-games_count")
    )

    return render(
        request,
        "player/details.html",
        {
            "player": player,
            "rating_results": rating_results,
            "external_rating_results": external_rating_results,
            "tournament_results": tournament_results,
            "tenhou_data": tenhou_data,
            "rating_date": entered_date,
            "external_rating_date": external_entered_date,
            "ms_data": ms_data,
            "club_ratings": club_ratings,
        },
    )


def player_tournaments(request, slug):
    player = get_object_or_404(Player, slug=slug)

    tournament_results = (
        TournamentResult.objects.filter(player=player).prefetch_related("tournament").order_by("-tournament__end_date")
    )

    return render(request, "player/tournaments.html", {"player": player, "tournament_results": tournament_results})


def player_rating_details(request, slug, rating_slug, year=None, month=None, day=None):
    player = get_object_or_404(Player, slug=slug)
    rating = get_object_or_404(Rating, slug=rating_slug)

    today, rating_date, is_last = parse_rating_date(year, month, day)
    if not rating_date:
        today, rating_date = get_latest_rating_date(rating)

    rating_result = get_object_or_404(RatingResult, rating=rating, player=player, date=rating_date)

    rating_deltas = (
        RatingDelta.objects.filter(player=player, rating=rating, date=rating_date)
        .prefetch_related("player")
        .prefetch_related("tournament")
        .order_by("-tournament__end_date")
    )

    top_tournaments_number = 3 if rating.is_online() else 4
    top_tournament_ids = tuple(
        d.tournament_id
        for d in sorted(
            rating_deltas,
            reverse=True,
            key=lambda d: float(d.base_rank) * float(d.coefficient_obj.age) * float(d.coefficient_value),
        )
    )[:top_tournaments_number]

    last_rating_place = RatingResult.objects.filter(rating=rating, date=rating_date).order_by("place").last().place
    filtered_results = _get_rating_changes(rating, player, today)

    return render(
        request,
        "player/rating_details.html",
        {
            "player": player,
            "rating": rating,
            "rating_deltas": rating_deltas,
            "rating_result": rating_result,
            "filtered_results": filtered_results,
            "last_rating_place": last_rating_place,
            "top_tournament_ids": top_tournament_ids,
            "rating_date": rating_date,
            "today": today,
            "is_last": is_last,
        },
    )


def player_rating_changes(request, slug, rating_slug, year=None, month=None, day=None):
    player = get_object_or_404(Player, slug=slug)
    rating = get_object_or_404(Rating, slug=rating_slug)

    today, rating_date, is_last = parse_rating_date(year, month, day)
    if not rating_date:
        today, rating_date = get_latest_rating_date(rating)

    rating_result = get_object_or_404(RatingResult, rating=rating, player=player, date=rating_date)
    filtered_results = reversed(_get_rating_changes(rating, player, today))

    return render(
        request,
        "player/rating_changes.html",
        {
            "player": player,
            "rating": rating,
            "results": filtered_results,
            "rating_date": rating_date,
            "today": today,
            "rating_result": rating_result,
        },
    )


def _get_rating_changes(rating, player, today):
    tournament_coefficients = (
        TournamentCoefficients.objects.filter(tournament__results__player=player, rating=rating)
        .exclude(previous_age=None)
        .exclude(age=F("previous_age"))
        .order_by("date")
        .select_related("tournament")
    )
    tournament_coefficients_by_date = defaultdict(list)
    for tc in tournament_coefficients:
        tournament_coefficients_by_date[tc.date].append(
            {"tournament_name": tc.tournament.name, "age": float(tc.age), "previous_age": float(tc.previous_age)}
        )

    all_rating_results = (
        RatingResult.objects.filter(rating=rating, player=player).filter(date__lte=today).order_by("date")
    )

    filtered_results = []
    previous_score = -1
    previous_place = -1
    for x in all_rating_results:
        if x.score != previous_score or x.place != previous_place:
            filtered_results.append(
                {
                    "result": x,
                    "previous_score": previous_score,
                    "previous_place": previous_place,
                    "coefficients": tournament_coefficients_by_date.get(x.date),
                }
            )
        previous_score = x.score
        previous_place = x.place

    return filtered_results

def calculate_statistics(queryset):
    if not queryset.exists():
        return None

    stats = queryset.aggregate(
        total_games=Count('id'),
        average_place=Avg('place'),
        first_place=100.0 * Avg(
            Case(
                When(place=1, then=1),
                default=0,
                output_field=FloatField()
            )
        ),
        second_place=100.0 * Avg(
            Case(
                When(place=2, then=1),
                default=0,
                output_field=FloatField()
            )
        ),
        third_place=100.0 * Avg(
            Case(
                When(place=3, then=1),
                default=0,
                output_field=FloatField()
            )
        ),
        fourth_place=100.0 * Avg(
            Case(
                When(place=4, then=1),
                default=0,
                output_field=FloatField()
            )
        )
    )
    return stats


def player_tenhou_details(request, slug):
    player = get_object_or_404(Player, slug=slug)
    tenhou_data = (
        TenhouNickname.active_objects.filter(player=player)
        .order_by("-is_main")
        .prefetch_related("aggregated_statistics")
    )
    tenhou_data_all_time_stat_four = tenhou_data[0].all_time_stat_four() if tenhou_data else []

    ippan_ton = calculate_statistics(tenhou_data_all_time_stat_four
                                     .filter(game_rules__startswith="四般東"))

    ippan_nan = calculate_statistics(tenhou_data_all_time_stat_four
                                     .filter(game_rules__startswith="四般南"))

    joukyuu_ton = calculate_statistics(tenhou_data_all_time_stat_four
                                       .filter(game_rules__startswith="四上東"))

    joukyuu_nan = calculate_statistics(tenhou_data_all_time_stat_four
                                       .filter(game_rules__startswith="四上南"))

    tokujou_ton = calculate_statistics(tenhou_data_all_time_stat_four
                                       .filter(game_rules__startswith="四特東"))

    tokujou_nan = calculate_statistics(tenhou_data_all_time_stat_four
                                       .filter(game_rules__startswith="四特南"))

    houou_ton = calculate_statistics(tenhou_data_all_time_stat_four
                                     .filter(game_rules__startswith="四鳳東"))

    houou_nan = calculate_statistics(tenhou_data_all_time_stat_four
                                     .filter(game_rules__startswith="四鳳南"))

    return render(
        request,
        "player/tenhou.html",
        {
            "player": player,
            "tenhou_data": tenhou_data,
            "tenhou_data_all_time_stat_four": tenhou_data_all_time_stat_four,
            "RANKS": TenhouAggregatedStatistics.RANKS,
            "ippan_ton": ippan_ton,
            "ippan_nan": ippan_nan,
            "joukyuu_ton": joukyuu_ton,
            "joukyuu_nan": joukyuu_nan,
            "tokujou_ton": tokujou_ton,
            "tokujou_nan": tokujou_nan,
            "houou_ton": houou_ton,
            "houou_nan": houou_nan,
        },
    )


def player_ms_details(request, slug):
    player = get_object_or_404(Player, slug=slug)
    ms_data = MSAccount.objects.filter(player=player).first()
    return render(request, "player/ms.html", {"player": player, "ms_data": ms_data})
