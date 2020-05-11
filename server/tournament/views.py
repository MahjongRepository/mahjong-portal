from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.translation import gettext as _

from player.models import Player
from settings.models import City
from tournament.forms import TournamentRegistrationForm, OnlineTournamentRegistrationForm, TournamentApplicationForm
from tournament.models import Tournament, TournamentResult, TournamentRegistration, OnlineTournamentRegistration


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
        form = OnlineTournamentRegistrationForm(initial=initial)
    else:
        form = TournamentRegistrationForm(initial=initial)

    if tournament.is_online():
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

    return render(
        request,
        "tournament/announcement.html",
        {"tournament": tournament, "page": "tournament", "form": form, "registration_results": registration_results},
    )


@require_POST
@csrf_exempt
def tournament_registration(request, tournament_id):
    """
    csrf validation didn't work on the mobile safari, not sure why.
    Let's disable it for now, because it is not really important action
    """
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
            instance.player = Player.objects.get(
                first_name_ru=instance.first_name.title(), last_name_ru=instance.last_name.title()
            )
        except (Player.DoesNotExist, Player.MultipleObjectsReturned):
            # TODO if multiple players are here, let's try to filter by city
            pass

        try:
            instance.city_object = City.objects.get(name_ru=instance.city)
        except City.DoesNotExist:
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
