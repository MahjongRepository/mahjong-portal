# -*- coding: utf-8 -*-

from functools import wraps

from django.shortcuts import redirect
from django.urls import reverse

from tournament.models import Tournament


def tournament_manager_auth_required(view_func):
    def _checklogin(request, *args, **kwargs):
        redirect_url = redirect(reverse("do_login") + "?next={0}".format(request.path))

        if not request.user.is_authenticated:
            return redirect_url

        tournament_id = kwargs["tournament_id"]
        try:
            tournament = Tournament.objects.get(id=tournament_id)
        except Tournament.DoesNotExist:
            return redirect_url

        kwargs["tournament"] = tournament

        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)

        if not request.user.is_tournament_manager:
            return redirect_url

        managed_tournaments = request.user.managed_tournaments.filter(id=tournament_id)

        if not managed_tournaments.exists():
            return redirect_url

        return view_func(request, *args, **kwargs)

    return wraps(view_func)(_checklogin)
