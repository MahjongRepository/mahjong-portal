# -*- coding: utf-8 -*-

from django.http import Http404, JsonResponse
from django.http.response import HttpResponseNotFound
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from rating.calculation.crr import RatingCRRCalculation
from rating.calculation.hardcoded_coefficients import HARDCODED_COEFFICIENTS
from rating.calculation.online import RatingOnlineCalculation
from rating.calculation.rr import RatingRRCalculation
from rating.models import (
    ExternalRating,
    ExternalRatingDate,
    ExternalRatingDelta,
    ExternalRatingTournament,
    Rating,
    RatingDate,
    RatingDelta,
    RatingResult,
    TournamentCoefficients,
)
from rating.utils import get_latest_rating_date, parse_rating_date
from settings.models import Country
from tournament.models import Tournament


def rating_list(request):
    ratings = Rating.objects.all().order_by("order")
    external_ratings = ExternalRating.objects.filter(is_hidden=False).all().order_by("order")

    return render(
        request, "rating/list.html", {"ratings": ratings, "external_ratings": external_ratings, "page": "rating"}
    )


def is_default_raing(slug):
    return slug.upper() in [x[1] for x in Rating.TYPES]


def rating_details(request, slug, year=None, month=None, day=None, country_code=None):
    is_default_rating = is_default_raing(slug)
    if is_default_rating:
        return get_rating_details(request, slug, year=year, month=month, day=day, country_code=country_code)
    else:
        rating = ExternalRating.objects.filter(slug=slug).first()
        if rating:
            return get_external_rating_details(
                rating, request, slug, year=year, month=month, day=day, country_code=country_code
            )
    return HttpResponseNotFound()


def get_external_rating_details(rating, request, slug, year=None, month=None, day=None, country_code=None):
    today, rating_date, is_last = parse_rating_date(year, month, day)
    if not rating_date:
        today, rating_date = get_latest_rating_date(rating, is_external=True)
    rating_results = ExternalRatingDelta.objects.filter(rating=rating, date=rating_date).order_by("-base_rank")
    return render(
        request,
        "rating/external_details.html",
        {
            "rating": rating,
            "rating_results": rating_results,
            "rating_date": rating_date,
            "is_last": is_last,
            "page": "rating",
            "countries_data": None,
            "closest_date": None,
            "country_code": country_code,
            "today": today,
            "is_ema": None,
            "show_tournaments_numbers": True,
        },
    )


def get_rating_details(request, slug, year=None, month=None, day=None, country_code=None):
    rating = get_object_or_404(Rating, slug=slug)

    today, rating_date, is_last = parse_rating_date(year, month, day)
    if not rating_date:
        today, rating_date = get_latest_rating_date(rating)

    is_ema = rating.type == Rating.EMA
    rating_results = (
        RatingResult.objects.filter(rating=rating)
        .prefetch_related("player")
        .prefetch_related("player__city")
        .prefetch_related("player__country")
        .order_by("place")
    )

    closest_date = RatingResult.objects.filter(rating=rating, date__lte=rating_date).order_by("date")
    if closest_date.exists():
        rating_date = closest_date.last().date
    else:
        raise Http404

    rating_results = rating_results.filter(date=rating_date)

    if rating.is_online():
        rating_results = rating_results.prefetch_related("player__tenhou")

    countries_data = {}
    if rating.type == Rating.EMA:
        countries_data = {}
        for rating_result in rating_results:
            country = rating_result.player.country
            if country.code not in countries_data:
                countries_data[country.code] = {"players": 0, "country": country}

            countries_data[country.code]["players"] += 1

        countries_data = sorted(countries_data.values(), key=lambda x: x["players"], reverse=True)

        if country_code:
            try:
                country = Country.objects.get(code=country_code)
                rating_results = rating_results.filter(player__country=country)
            except Country.DoesNotExist:
                pass

    render_as_json = request.GET.get("json")
    if render_as_json is not None:
        data = []
        for rating_result in rating_results:
            data.append(
                {
                    "id": rating_result.player.id,
                    "place": rating_result.place,
                    "scores": float(rating_result.score),
                    "name": rating_result.player.full_name,
                    "city": rating_result.player.city.name,
                }
            )
        return JsonResponse(data, safe=False)

    return render(
        request,
        "rating/details.html",
        {
            "rating": rating,
            "rating_results": rating_results,
            "rating_date": rating_date,
            "is_last": is_last,
            "page": "rating",
            "countries_data": countries_data,
            "closest_date": closest_date,
            "country_code": country_code,
            "today": today,
            "is_ema": is_ema,
            "show_tournaments_numbers": True,
        },
    )


def rating_dates(request, slug):
    is_default_rating = is_default_raing(slug)
    if is_default_rating:
        rating = get_object_or_404(Rating, slug=slug)
        rating_dates = RatingDate.objects.filter(rating=rating).order_by("-date")
    else:
        rating = get_object_or_404(ExternalRating, slug=slug)
        rating_dates = ExternalRatingDate.objects.filter(rating=rating).order_by("-date")
    return render(request, "rating/dates.html", {"rating": rating, "rating_dates": rating_dates})


def get_external_rating_tournaments(request, rating):
    tournament_ids = ExternalRatingTournament.objects.filter(rating=rating).values_list("tournament_id", flat=True)
    tournaments = (
        Tournament.objects.filter(id__in=tournament_ids)
        .prefetch_related("city")
        .prefetch_related("country")
        .order_by("-end_date")
    )

    return render(
        request,
        "rating/rating_tournaments.html",
        {
            "rating": rating,
            "tournaments": tournaments,
            "page": "rating",
            "coefficients": None,
            "top_tournament_ids": None,
        },
    )


def rating_tournaments(request, slug):
    is_default_rating = is_default_raing(slug)
    if not is_default_rating:
        rating = get_object_or_404(ExternalRating, slug=slug)
        return get_external_rating_tournaments(request, rating)

    rating = get_object_or_404(Rating, slug=slug)
    today, rating_date = get_latest_rating_date(rating)
    tournament_ids = (
        RatingDelta.objects.filter(date=rating_date)
        .filter(rating=rating)
        .filter(is_active=True)
        .values_list("tournament_id", flat=True)
    )
    tournaments = (
        Tournament.public.filter(id__in=tournament_ids)
        .prefetch_related("city")
        .prefetch_related("country")
        .order_by("-end_date")
    )

    coefficients = (
        TournamentCoefficients.objects.filter(
            tournament_id__in=tournament_ids, rating=rating, date__lte=timezone.now().date()
        )
        .order_by("tournament_id", "-date")
        .distinct("tournament_id")
    )

    if rating.type == Rating.EMA:
        coefficients_dict = {}
        top_tournament_ids = []
    else:
        stages_tournament_ids = HARDCODED_COEFFICIENTS.keys()

        coefficients_dict = {}
        for coefficient in coefficients:
            coefficients_dict[coefficient.tournament_id] = {
                "value": (float(coefficient.age) / 100.0) * float(coefficient.coefficient),
                "age": coefficient.age,
                "coefficient": coefficient.coefficient,
                "tournament_id": coefficient.tournament_id,
            }

            if coefficient.tournament_id in stages_tournament_ids:
                stage_coefficients = list(set(HARDCODED_COEFFICIENTS[coefficient.tournament_id].values()))
                for x in stage_coefficients:
                    value = (float(coefficient.age) / 100.0) * float(x)
                    coefficients_dict[coefficient.tournament_id] = {
                        "coefficient": x,
                        "age": coefficient.age,
                        "value": value,
                        "tournament_id": coefficient.tournament_id,
                    }

        top_tournaments_number = {
            Rating.RR: RatingRRCalculation.SECOND_PART_MIN_TOURNAMENTS,
            Rating.CRR: RatingCRRCalculation.SECOND_PART_MIN_TOURNAMENTS,
            Rating.ONLINE: RatingOnlineCalculation.SECOND_PART_MIN_TOURNAMENTS,
        }.get(rating.type)

        top_coefficients = sorted(coefficients_dict.values(), key=lambda t: t["value"], reverse=True)[
            :top_tournaments_number
        ]

        top_tournament_ids = [c["tournament_id"] for c in top_coefficients]

    return render(
        request,
        "rating/rating_tournaments.html",
        {
            "rating": rating,
            "tournaments": tournaments,
            "page": "rating",
            "coefficients": coefficients_dict,
            "top_tournament_ids": top_tournament_ids,
        },
    )
