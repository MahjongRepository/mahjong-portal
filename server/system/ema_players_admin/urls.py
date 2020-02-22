from django.conf.urls import url

from system.ema_players_admin.views import (
    list_of_ema_players,
    download_players_list_csv,
    add_new_player,
    assign_ema_id,
)

urlpatterns = [
    url(r"^list/$", list_of_ema_players, name="list_of_ema_players"),
    url(r"^list/csv/$", download_players_list_csv, name="download_players_list_csv"),
    url(r"^add/$", add_new_player, name="add_new_player"),
    url(r"^assign_id/(?P<player_id>\d+)/$", assign_ema_id, name="assign_ema_id"),
]
