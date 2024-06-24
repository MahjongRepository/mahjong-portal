# -*- coding: utf-8 -*-

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from account.models import PantheonInfoUpdateLog
from pantheon_api.api_calls.user import get_pantheon_public_person_information
from player.models import Player
from settings.models import City
from tournament.forms import (
    MajsoulOnlineTournamentPantheonRegistrationForm,
    OnlineTournamentPantheonRegistrationForm,
    OnlineTournamentRegistrationForm,
    TournamentApplicationForm,
    TournamentRegistrationForm,
)
from tournament.models import (
    MsOnlineTournamentRegistration,
    OnlineTournamentRegistration,
    Tournament,
    TournamentRegistration,
    TournamentResult,
)
from utils.general import split_name


def tournament_list(request, tournament_type=None, year=None):
    current_year = timezone.now().year
    try:
        selected_year = year and int(year)
    except ValueError:
        selected_year = current_year

    years = []
    for x in range(10):
        years.append(current_year - x)

    tournaments = Tournament.objects.filter(end_date__year=selected_year)

    if tournament_type == "ema":
        tournament_types = [Tournament.EMA, Tournament.FOREIGN_EMA, Tournament.CHAMPIONSHIP]
        tournaments = tournaments.filter(tournament_type__in=tournament_types)
    else:
        tournament_types = [Tournament.EMA, Tournament.RR, Tournament.CRR, Tournament.OTHER, Tournament.ONLINE]
        tournaments = tournaments.filter(tournament_type__in=tournament_types)

    tournaments = tournaments.order_by("-end_date").prefetch_related("city").prefetch_related("country")

    upcoming_tournaments = (
        Tournament.public.filter(is_upcoming=True)
        .filter(is_event=False)
        .exclude(tournament_type=Tournament.FOREIGN_EMA)
        .prefetch_related("city")
        .order_by("start_date")
    )
    tournaments = tournaments.filter(is_upcoming=False)

    return render(
        request,
        "tournament/list.html",
        {
            "tournaments": tournaments,
            "upcoming_tournaments": upcoming_tournaments,
            "tournament_type": tournament_type,
            "years": years,
            "selected_year": selected_year,
            "page": tournament_type or "tournament",
        },
    )


def tournament_details(request, slug):
    tournament = get_object_or_404(Tournament, slug=slug)
    if tournament.is_upcoming:
        return redirect(tournament_announcement, slug=slug)

    results = (
        TournamentResult.objects.filter(tournament=tournament)
        .order_by("place")
        .prefetch_related("player__city")
        .prefetch_related("player__country")
        .prefetch_related("player")
    )

    countries = {}
    for result in results:
        if not result.player:
            continue

        country = result.player.country
        if not country:
            continue

        if not countries.get(country.id):
            countries[country.id] = {"count": 0, "name": country.name, "code": country.code}

        countries[country.id]["count"] += 1

    countries = sorted(countries.values(), key=lambda x: x["count"], reverse=True)

    return render(
        request,
        "tournament/details.html",
        {"tournament": tournament, "results": results, "page": "tournament", "countries": countries},
    )


def tournament_announcement(request, slug):
    tournament = get_object_or_404(Tournament, slug=slug)

    initial = {"tournament": tournament}
    if tournament.city and tournament.fill_city_in_registration:
        initial["city"] = tournament.city.name_ru

    if tournament.is_online():
        if tournament.is_majsoul_tournament and tournament.is_pantheon_registration:
            form = MajsoulOnlineTournamentPantheonRegistrationForm(initial=initial)
        elif not tournament.is_majsoul_tournament and tournament.is_pantheon_registration:
            form = OnlineTournamentPantheonRegistrationForm(initial=initial)
        else:
            form = OnlineTournamentRegistrationForm(initial=initial)
    else:
        form = TournamentRegistrationForm(initial=initial)

    if tournament.is_online():
        if tournament.is_majsoul_tournament:
            registration_results = (
                MsOnlineTournamentRegistration.objects.filter(tournament=tournament)
                .filter(is_approved=True)
                .prefetch_related("player")
                .prefetch_related("city_object")
                .order_by("created_on")
            )
        else:
            registration_results = (
                OnlineTournamentRegistration.objects.filter(tournament=tournament)
                .filter(is_approved=True)
                .prefetch_related("player")
                .prefetch_related("city_object")
                .order_by("created_on")
            )
        if tournament.display_notes:
            registration_results = registration_results.order_by("notes", "created_on")
    else:
        registration_results = (
            TournamentRegistration.objects.filter(tournament=tournament)
            .filter(is_approved=True)
            .prefetch_related("player")
            .prefetch_related("city_object")
            .order_by("created_on")
        )
        if tournament.display_notes:
            registration_results = registration_results.order_by("notes", "created_on")

    is_already_registered = False
    if request.user.is_authenticated:
        # TODO support not only online tournaments
        if tournament.is_majsoul_tournament:
            is_already_registered = MsOnlineTournamentRegistration.objects.filter(
                tournament=tournament, user=request.user
            ).exists()
        else:
            is_already_registered = OnlineTournamentRegistration.objects.filter(
                tournament=tournament, user=request.user
            ).exists()

    missed_tenhou_id_error = request.GET.get("error") == "tenhou_id"
    form_data_error = request.GET.get("error") == "form_data"

    return render(
        request,
        "tournament/announcement.html",
        {
            "tournament": tournament,
            "page": "tournament",
            "form": form,
            "registration_results": registration_results,
            "is_already_registered": is_already_registered,
            "missed_tenhou_id_error": missed_tenhou_id_error,
            "form_data_error": form_data_error,
        },
    )


@require_POST
@login_required
def pantheon_tournament_registration(request, tournament_id):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    user = request.user
    form_data = request.POST
    notes = None

    if tournament.display_notes:
        notes = form_data["notes"]

    if tournament.is_majsoul_tournament:
        try:
            ms_friend_id = int(form_data["ms_friend_id"])
            ms_nickname = form_data["ms_nickname"]
            if form_data.get("allow_to_save_data") is None:
                allow_to_save_data = False
            else:
                allow_to_save_data = bool(form_data["allow_to_save_data"])
            if not bool(ms_nickname.strip()):
                return redirect(tournament.get_url() + "?error=form_data")
        except Exception:
            return redirect(tournament.get_url() + "?error=form_data")

    if tournament.is_majsoul_tournament:
        if MsOnlineTournamentRegistration.objects.filter(user=user, tournament=tournament).exists():
            return redirect(tournament.get_url())
    else:
        if OnlineTournamentRegistration.objects.filter(user=user, tournament=tournament).exists():
            return redirect(tournament.get_url())

    # todo get ms_data and store into PantheonInfoUpdateLog
    data = get_pantheon_public_person_information(user.new_pantheon_id)
    PantheonInfoUpdateLog.objects.create(user=user, pantheon_id=user.new_pantheon_id, updated_information=data)
    first_name, last_name = split_name(data["title"])

    player = Player.objects.filter(first_name_ru=first_name, last_name_ru=last_name).first()
    if not player:
        player = Player.objects.filter(first_name_ru=last_name, last_name_ru=first_name).first()
    city_object = City.objects.filter(name_ru=data["city"].title()).first()

    if not tournament.is_majsoul_tournament and not data["tenhou_id"]:
        return redirect(tournament.get_url() + "?error=tenhou_id")

    if tournament.is_majsoul_tournament:
        # todo get ms_data from pantheon
        MsOnlineTournamentRegistration.objects.create(
            tournament=tournament,
            user=user,
            ms_nickname=ms_nickname,
            ms_friend_id=ms_friend_id,
            first_name=first_name,
            last_name=last_name,
            city=data["city"],
            player=player,
            city_object=city_object,
            allow_to_save_data=allow_to_save_data,
            notes=notes,
        )
    else:
        OnlineTournamentRegistration.objects.create(
            tournament=tournament,
            user=user,
            tenhou_nickname=data["tenhou_id"],
            first_name=first_name,
            last_name=last_name,
            city=data["city"],
            player=player,
            city_object=city_object,
            notes=notes,
        )

    return redirect(tournament.get_url())


@require_POST
def tournament_registration(request, tournament_id):
    tournament = get_object_or_404(Tournament, id=tournament_id)

    if tournament.is_online():
        form = OnlineTournamentRegistrationForm(request.POST, initial={"tournament": tournament})
    else:
        form = TournamentRegistrationForm(request.POST, initial={"tournament": tournament})

    if form.is_valid():
        if tournament.is_online():
            tenhou_nickname = form.cleaned_data.get("tenhou_nickname")
            exists = OnlineTournamentRegistration.objects.filter(
                tournament=tournament, tenhou_nickname=tenhou_nickname
            ).exists()
            if exists:
                messages.success(request, _("You already registered to the tournament!"))
                return redirect(tournament.get_url())

        instance = form.save(commit=False)
        instance.tournament = tournament

        # it supports auto load objects only for Russian tournaments right now

        try:
            if instance.city:
                instance.city_object = City.objects.get(name_ru=instance.city)
        except City.DoesNotExist:
            pass

        try:
            if instance.city_object:
                instance.player = Player.objects.get(
                    first_name_ru=instance.first_name.title(),
                    last_name_ru=instance.last_name.title(),
                    city=instance.city_object,
                )
            else:
                instance.player = Player.objects.get(
                    first_name_ru=instance.first_name.title(), last_name_ru=instance.last_name.title()
                )
        except (Player.DoesNotExist, Player.MultipleObjectsReturned):
            # TODO if multiple players are here, let's try to filter by city
            pass

        if tournament.registrations_pre_moderation:
            instance.is_approved = False
            message = _(
                "Your registration was accepted! It will be visible on the page after administrator approvement."
            )
        else:
            instance.is_approved = True
            message = _("Your registration was accepted!")

        instance.save()

        messages.success(request, message)
    else:
        messages.success(request, _("Please, allow to store personal data"))

    return redirect(tournament.get_url())


def tournament_application(request):
    success = False
    form = TournamentApplicationForm()

    if request.POST:
        form = TournamentApplicationForm(request.POST)
        if form.is_valid():
            form.save()
            success = True

    return render(request, "tournament/application.html", {"form": form, "success": success})
