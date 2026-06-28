# -*- coding: utf-8 -*-

import csv
import dataclasses
import logging
import typing as ty

from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import MultipleObjectsReturned
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from player.models import Player
from system.decorators import tournament_manager_auth_required
from system.tournament_admin.forms import (
    MsOnlineTournamentRegistrationNotesForm,
    OnlineTournamentRegistrationNotesForm,
    TournamentForm,
    TournamentRegistrationNotesForm,
    UploadResultsForm,
)
from tournament.models import (
    MsOnlineTournamentRegistration,
    OnlineTournamentRegistration,
    Tournament,
    TournamentRegistration,
    TournamentResult,
)
from utils.general import transliterate_name

logger = logging.getLogger()


@dataclasses.dataclass
class FilteredResult:
    place: int = None
    player_pantheon_id: int = None
    first_name: str = None
    last_name: str = None
    scores: float = None
    ema_id: str = None
    games: int = None
    load_player: bool = None


def update_placing(rows: ty.List[FilteredResult]) -> None:
    """Update players placing according to their score."""
    rows.sort(key=lambda row: (-row.games, -row.scores))  # ORDER BY games DESC, scores DESC
    place, scores, games = 0, None, None
    for i, row in enumerate(rows, start=1):
        if row.scores != scores or row.games != games:
            place, scores, games = i, row.scores, row.games
        row.place = place


def get_csv_field(row: ty.Dict[str, ty.Any], possible_fields: ty.List[str], default=None) -> ty.Any:
    for field in possible_fields:
        if field in row:
            return row[field]
    return default


@login_required
@user_passes_test(lambda u: u.is_superuser)
def new_tournaments(request):
    tournaments = Tournament.objects.filter(is_upcoming=True, is_hidden=False).order_by("start_date")
    return render(request, "tournament_admin/new_tournaments.html", {"tournaments": tournaments})


@login_required
@user_passes_test(lambda u: u.is_superuser)
def upload_results(request, tournament_id):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    form = UploadResultsForm()

    not_found_users = []
    file_was_uploaded = False
    success = False

    if request.POST:
        form = UploadResultsForm(request.POST, request.FILES)
        if form.is_valid():
            file_was_uploaded = True

            csv_file = form.cleaned_data["csv_file"]

            is_ema = form.cleaned_data["ema"]
            decoded_file = csv_file.read().decode("utf-8").splitlines()
            reader = csv.DictReader(decoded_file)

            filtered_results: ty.List[FilteredResult] = []
            for row in reader:
                place = int(get_csv_field(row, possible_fields=["place", "Place"]))
                name = get_csv_field(row, possible_fields=["name", "Player name"], default="")
                scores = float(get_csv_field(row, possible_fields=["scores", "Rating points"]))
                games = int(get_csv_field(row, possible_fields=["games", "Games played"], default=0))
                player_pantheon_id = int(get_csv_field(row, possible_fields=["player_id", "Player ID"]))

                ema_id = row.get("ema", "").strip()
                load_player = row.get("load_player", "true").strip().lower()
                load_player = load_player == "true"

                if is_ema:
                    first_name = row["first_name"].title()
                    last_name = row["last_name"].title()
                else:
                    temp = name.split(" ")

                    if load_player:
                        extracted_first_name = temp[1].title()
                        extracted_last_name = temp[0].title()
                    elif not load_player and len(temp) < 2:
                        extracted_first_name = temp[0].title()
                        extracted_last_name = ""
                    else:
                        extracted_first_name = temp[1].title()
                        extracted_last_name = temp[0].title()

                    if form.cleaned_data["switch_names"]:
                        first_name = extracted_last_name
                        last_name = extracted_first_name
                    else:
                        first_name = extracted_first_name
                        last_name = extracted_last_name

                    if first_name == "Замены":
                        first_name = "замены"

                first_name = first_name.strip()
                last_name = last_name.strip()

                filtered_results.append(
                    FilteredResult(
                        place=place,
                        player_pantheon_id=player_pantheon_id,
                        first_name=first_name,
                        last_name=last_name,
                        scores=scores,
                        ema_id=ema_id,
                        games=games,
                        load_player=load_player,
                    )
                )

                if not load_player:
                    continue

                try:
                    if is_ema:
                        if ema_id:
                            Player.objects.get(ema_id=ema_id)
                        else:
                            Player.objects.get(first_name_en=first_name, last_name_en=last_name)
                    else:
                        try:
                            Player.objects.get(first_name_ru=first_name, last_name_ru=last_name)
                        except MultipleObjectsReturned as e:
                            logger.error(f"Multiple players found: [{first_name} {last_name}]")
                            raise e
                except Player.DoesNotExist:
                    if is_ema:
                        not_found_users.append("{} {} {}".format(first_name, last_name, ema_id))
                    else:
                        not_found_users.append(
                            "{} {} {} {}".format(
                                transliterate_name(first_name), first_name, transliterate_name(last_name), last_name
                            )
                        )

            auto_placing: bool = form.cleaned_data.get("auto_placing", False)
            if auto_placing:
                update_placing(filtered_results)

            # everything is fine
            if not not_found_users:
                for result in filtered_results:
                    place = result.place
                    player_pantheon_id = result.player_pantheon_id
                    first_name = result.first_name
                    last_name = result.last_name
                    scores = result.scores
                    ema_id = result.ema_id
                    games = result.games
                    load_player = result.load_player

                    player = None
                    player_string = None
                    if load_player:
                        if is_ema:
                            if ema_id:
                                player = Player.objects.get(ema_id=ema_id)
                            else:
                                player = Player.objects.get(first_name_en=first_name, last_name_en=last_name)
                        else:
                            player = Player.objects.get(first_name_ru=first_name, last_name_ru=last_name)
                    else:
                        player_string = "{} {}".format(last_name, first_name)

                    TournamentResult.objects.create(
                        player=player,
                        player_string=player_string,
                        tournament=tournament,
                        place=place,
                        scores=scores,
                        games=games,
                        player_pantheon_id=player_pantheon_id,
                    )

                tournament.is_upcoming = False
                tournament.opened_registration = False
                tournament.is_apply_in_rating = False
                tournament.number_of_players = len(filtered_results)
                tournament.save()

                success = True

    return render(
        request,
        "tournament_admin/upload_results.html",
        {
            "tournament": tournament,
            "form": form,
            "not_found_users": not_found_users,
            "file_was_uploaded": file_was_uploaded,
            "success": success,
        },
    )


@login_required
@user_passes_test(lambda u: u.is_superuser or u.is_tournament_manager)
def managed_tournaments(request):
    tournaments = request.user.managed_tournaments.all().order_by("-end_date")
    return render(request, "tournament_admin/managed_tournaments.html", {"tournaments": tournaments})


@login_required
@tournament_manager_auth_required
def tournament_manage(request, tournament_id, **kwargs):
    tournament = kwargs["tournament"]

    if tournament.is_online():
        if tournament.is_majsoul_tournament:
            tournament_registrations = MsOnlineTournamentRegistration.objects.filter(tournament=tournament).order_by(
                "-created_on"
            )
        else:
            tournament_registrations = OnlineTournamentRegistration.objects.filter(tournament=tournament).order_by(
                "-created_on"
            )
    else:
        tournament_registrations = TournamentRegistration.objects.filter(tournament=tournament).order_by("-created_on")

    return render(
        request,
        "tournament_admin/tournament_manage.html",
        {"tournament": tournament, "tournament_registrations": tournament_registrations},
    )


@login_required
@tournament_manager_auth_required
def tournament_edit(request, tournament_id, **kwargs):
    tournament = kwargs["tournament"]
    form = TournamentForm(instance=tournament)
    if request.POST:
        form = TournamentForm(request.POST, instance=tournament)
        if form.is_valid():
            form.save()
            return redirect(tournament_manage, tournament.id)
    return render(request, "tournament_admin/tournament_edit.html", {"tournament": tournament, "form": form})


@login_required
@tournament_manager_auth_required
def toggle_registration(request, tournament_id, **kwargs):
    tournament = kwargs["tournament"]
    tournament.opened_registration = not tournament.opened_registration

    # We need to publish tournament once admin open registration
    if tournament.opened_registration and tournament.is_hidden:
        tournament.is_hidden = False

    tournament.save()

    return redirect(tournament_manage, tournament.id)


@login_required
@tournament_manager_auth_required
def toggle_premoderation(request, tournament_id, **kwargs):
    tournament = kwargs["tournament"]
    tournament.registrations_pre_moderation = not tournament.registrations_pre_moderation
    tournament.save()
    return redirect(tournament_manage, tournament.id)


@login_required
@tournament_manager_auth_required
def remove_registration(request, tournament_id, registration_id, **kwargs):
    tournament = kwargs["tournament"]

    item_class = TournamentRegistration
    if tournament.is_online():
        if tournament.is_majsoul_tournament:
            item_class = MsOnlineTournamentRegistration
        else:
            item_class = OnlineTournamentRegistration

    registration = get_object_or_404(item_class, tournament=tournament, id=registration_id)
    registration.delete()
    return redirect(tournament_manage, tournament.id)


@login_required
@tournament_manager_auth_required
def toggle_highlight(request, tournament_id, registration_id, **kwargs):
    tournament = kwargs["tournament"]

    try:
        registration = get_object_or_404(TournamentRegistration, tournament=tournament, id=registration_id)
    except Http404:
        registration = get_object_or_404(OnlineTournamentRegistration, tournament=tournament, id=registration_id)

    registration.is_highlighted = not registration.is_highlighted
    registration.save()

    return redirect(tournament_manage, tournament.id)


@login_required
@tournament_manager_auth_required
def approve_registration(request, tournament_id, registration_id, **kwargs):
    tournament = kwargs["tournament"]

    item_class = TournamentRegistration
    if tournament.is_online():
        if tournament.is_majsoul_tournament:
            item_class = MsOnlineTournamentRegistration
        else:
            item_class = OnlineTournamentRegistration

    registration = get_object_or_404(item_class, tournament=tournament, id=registration_id)
    registration.is_approved = True
    registration.save()
    return redirect(tournament_manage, tournament.id)


@login_required
@tournament_manager_auth_required
def toggle_share_notes(request, tournament_id, **kwargs):
    tournament = kwargs["tournament"]
    if tournament.display_notes:
        tournament.share_notes = not tournament.share_notes
        tournament.save()
    return redirect(tournament_manage, tournament.id)


@login_required
@tournament_manager_auth_required
def notes_edit(request, tournament_id, registration_id, **kwargs):
    tournament = kwargs["tournament"]

    item_class = TournamentRegistration
    if tournament.is_online():
        if not tournament.is_majsoul_tournament:
            item_class = OnlineTournamentRegistration
        else:
            item_class = MsOnlineTournamentRegistration

    registration = get_object_or_404(item_class, tournament=tournament, id=registration_id)

    form = TournamentRegistrationNotesForm(instance=registration)
    if tournament.is_online():
        if not tournament.is_majsoul_tournament:
            form = OnlineTournamentRegistrationNotesForm(instance=registration)
        else:
            form = MsOnlineTournamentRegistrationNotesForm(instance=registration)

    if request.POST:
        form = TournamentRegistrationNotesForm(request.POST, instance=registration)
        if tournament.is_online():
            if not tournament.is_majsoul_tournament:
                form = OnlineTournamentRegistrationNotesForm(request.POST, instance=registration)
            else:
                form = MsOnlineTournamentRegistrationNotesForm(request.POST, instance=registration)
        if form.is_valid():
            form.save()
            return redirect(tournament_manage, tournament.id)
    return render(
        request,
        "tournament_admin/tournament_registration_notes_edit.html",
        {"tournament": tournament, "registration": registration, "form": form},
    )


@login_required
@tournament_manager_auth_required
def toggle_hidden(request, tournament_id, **kwargs):
    tournament = kwargs["tournament"]
    if not tournament.is_hidden:
        tournament.opened_registration = False
    tournament.is_hidden = not tournament.is_hidden
    tournament.save()

    return redirect(tournament_manage, tournament.id)
