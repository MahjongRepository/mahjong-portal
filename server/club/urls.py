from django.conf.urls import url

from club.views import club_details, club_list, club_tournaments

urlpatterns = [
    url(r"^riichi/$", club_list, name="club_list"),
    url(r"^riichi/(?P<slug>[\w\-]+)/$", club_details, name="club_details"),
    url(r"^riichi/(?P<slug>[\w\-]+)/tournaments/$", club_tournaments, name="club_tournaments"),
]
