# -*- coding: utf-8 -*-

from django.urls import re_path as url

from player.mahjong_soul.views import ms_accounts

urlpatterns = [
    url(r"^accounts/$", ms_accounts, name="ms_accounts"),
    url(r"^accounts/(?P<stat_type>[\w\-]+)/$", ms_accounts, name="ms_accounts"),
]
