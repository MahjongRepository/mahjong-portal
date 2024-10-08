# -*- coding: utf-8 -*-

from django.urls import re_path as url

from player.tenhou.views import (
    games_history,
    get_current_tenhou_games,
    get_current_tenhou_games_async,
    latest_yakumans,
    tenhou_accounts,
)

urlpatterns = [
    url(r"^games/history/(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/$", games_history, name="tenhou_games_history"),
    url(r"^games/history/$", games_history, name="tenhou_games_history"),
    url(r"^games/$", get_current_tenhou_games, name="get_current_tenhou_games"),
    url(r"^games/async/$", get_current_tenhou_games_async, name="get_current_tenhou_games_async"),
    url(r"^yakumans/$", latest_yakumans, name="latest_yakumans"),
    url(r"^accounts/$", tenhou_accounts, name="tenhou_accounts"),
]
