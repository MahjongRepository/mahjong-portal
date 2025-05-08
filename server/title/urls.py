# -*- coding: utf-8 -*-

from django.urls import re_path as url

from title.views import titles_list

urlpatterns = [
    url(r"^$", titles_list, name="titles_list"),
]
