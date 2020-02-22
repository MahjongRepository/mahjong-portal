from django.conf.urls import url

from system.tournament_admin.views import (
    new_tournaments,
    upload_results,
    managed_tournaments,
    tournament_manage,
    toggle_registration,
    toggle_premoderation,
    tournament_edit,
    remove_registration,
    approve_registration,
    toggle_highlight,
)

urlpatterns = [
    url(r"^list/$", new_tournaments, name="new_tournaments"),
    url(r"^managed/$", managed_tournaments, name="managed_tournaments"),
    url(
        r"^managed/(?P<tournament_id>\d+)/$",
        tournament_manage,
        name="tournament_manage",
    ),
    url(
        r"^managed/(?P<tournament_id>\d+)/edit/$",
        tournament_edit,
        name="tournament_edit",
    ),
    url(
        r"^managed/(?P<tournament_id>\d+)/registration/(?P<registration_id>\d+)/remove/$",
        remove_registration,
        name="remove_registration",
    ),
    url(
        r"^managed/(?P<tournament_id>\d+)/registration/(?P<registration_id>\d+)/highlight/$",
        toggle_highlight,
        name="toggle_highlight",
    ),
    url(
        r"^managed/(?P<tournament_id>\d+)/registration/(?P<registration_id>\d+)/approve/$",
        approve_registration,
        name="approve_registration",
    ),
    url(
        r"^managed/(?P<tournament_id>\d+)/registration/toggle$",
        toggle_registration,
        name="toggle_registration",
    ),
    url(
        r"^managed/(?P<tournament_id>\d+)/premoderation/toggle$",
        toggle_premoderation,
        name="toggle_premoderation",
    ),
    url(r"^(?P<tournament_id>\d+)/upload/$", upload_results, name="upload_results"),
]
