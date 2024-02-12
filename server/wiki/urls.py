# -*- coding: utf-8 -*-

from django.urls import path

from wiki.views import wiki_home

urlpatterns = [
    path("", wiki_home, name="wiki_home"),
]
