# -*- coding: utf-8 -*-

from django.conf.urls import include
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import re_path as url
from django.views.decorators.cache import cache_page

from mahjong_portal.sitemap import (
    ClubSitemap,
    EMATournamentListSitemap,
    PlayerSitemap,
    RatingSitemap,
    StaticSitemap,
    TournamentAnnouncementSitemap,
    TournamentListSitemap,
    TournamentSitemap,
)
from online.views import (
    admin_confirm_player,
    check_new_notifications,
    close_registration,
    confirm_player,
    create_start_ms_game_notification,
    finish_game_api,
    game_finish,
    get_allowed_players,
    get_tournament_status,
    open_registration,
    prepare_next_round,
    process_notification,
)
from website.views import players_api, update_info_from_pantheon_api

sitemaps = {
    "static": StaticSitemap,
    "tournament_list": TournamentListSitemap,
    "ema_tournaments_list": EMATournamentListSitemap,
    "tournament_details": TournamentSitemap,
    "tournament_announcement_details": TournamentAnnouncementSitemap,
    "club_details": ClubSitemap,
    "player_details": PlayerSitemap,
    "rating_details": RatingSitemap,
}

urlpatterns = [
    url(r"^admin/", include(admin.site.urls[:2])),
    url(r"^i18n/", include("django.conf.urls.i18n")),
    url(
        r"^sitemap\.xml$",
        cache_page(86400)(sitemap),
        {"sitemaps": sitemaps},
        name="django.contrib.sitemaps.views.sitemap",
    ),
    url("^api/v0/players/$", players_api),
    url("^api/v0/update_info_from_pantheon/$", update_info_from_pantheon_api),
    url("^api/v0/finish_game_api/$", finish_game_api),
    url("^api/v0/autobot/open_registration$", open_registration),
    url("^api/v0/autobot/close_registration$", close_registration),
    url("^api/v0/autobot/check_notifications$", check_new_notifications),
    url("^api/v0/autobot/process_notification$", process_notification),
    url("^api/v0/autobot/prepare_next_round$", prepare_next_round),
    url("^api/v0/autobot/confirm_player$", confirm_player),
    url("^api/v0/autobot/admin_confirm_player$", admin_confirm_player),
    url("^api/v0/autobot/create_start_ms_game_notification$", create_start_ms_game_notification),
    url("^api/v0/autobot/game_finish$", game_finish),
    url("^api/v0/autobot/get_tournament_status$", get_tournament_status),
    url("^api/v0/autobot/get_tournament_players$", get_allowed_players),
    url(r"^online/", include("online.urls")),
]

urlpatterns += i18n_patterns(
    url(r"", include("website.urls")),
    url(r"^rating/", include("rating.urls")),
    url(r"^tournaments/", include("tournament.urls")),
    url(r"^clubs/", include("club.urls")),
    url(r"^players/", include("player.urls")),
    url(r"^tenhou/", include("player.tenhou.urls")),
    url(r"^ms/", include("player.mahjong_soul.urls")),
    url(r"^system/", include("system.urls")),
    url(r"^ema/", include("ema.urls")),
    url(r"^account/", include("account.urls")),
    url(r"^wiki/", include("wiki.urls")),
    url(r"^league/", include("league.urls")),
)
