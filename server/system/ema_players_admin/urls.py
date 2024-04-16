# -*- coding: utf-8 -*-

from django.urls import re_path as url

from system.ema_players_admin.views import add_new_player, assign_ema_id, download_players_list_csv, list_of_ema_players

urlpatterns = [
    url(r"^list/$", list_of_ema_players, name="list_of_ema_players"),
    url(r"^list/csv/$", download_players_list_csv, name="download_players_list_csv"),
    url(r"^add/$", add_new_player, name="add_new_player"),
    url(r"^assign_id/(?P<player_id>\d+)/$", assign_ema_id, name="assign_ema_id"),
]
