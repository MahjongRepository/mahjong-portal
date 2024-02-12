# -*- coding: utf-8 -*-

from django.urls import re_path as url

from website.views import (
    about,
    championships,
    city_page,
    contacts,
    ermc_qualification_2019,
    export_tournament_results,
    home,
    iormc_2018,
    online_tournament_rules,
    rating_faq,
    search,
    server,
    wrc_qualification_2020,
)

urlpatterns = [
    url(r"^$", home, name="home"),
    url(r"^about/$", about, name="about"),
    url(r"^iormc/2018/$", iormc_2018, name="iormc_2018"),
    url(r"^ermc/2019/$", ermc_qualification_2019, name="ermc_qualification_2019"),
    url(r"^wrc/2020/$", wrc_qualification_2020, name="wrc_qualification_2020"),
    url(r"^rating/faq/$", rating_faq, name="rating_faq"),
    url(r"^contacts/$", contacts, name="contacts"),
    url(r"^championships/$", championships, name="championships"),
    url(r"^online/$", online_tournament_rules, name="online"),
    url(r"^search/$", search, name="search"),
    url(r"^server/$", server, name="server"),
    url(r"^city/(?P<slug>[\w\-]+)/$", city_page, name="city_page"),
    url(
        r"^export_tournament_results/(?P<tournament_id>\d+)/$",
        export_tournament_results,
        name="export_tournament_results",
    ),
]
