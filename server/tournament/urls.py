from django.conf.urls import url

from tournament.views import (
    tournament_list,
    tournament_details,
    tournament_announcement,
    tournament_registration,
    tournament_application,
)

urlpatterns = [
    url(r"^new/$", tournament_application, name="tournament_application"),
    url(r"^riichi/(?P<year>\d+)/$", tournament_list, name="tournament_list"),
    url(r"^riichi/(?P<tournament_type>[\w\-]+)/(?P<year>\d+)/$", tournament_list, name="tournament_ema_list"),
    url(r"^registration/(?P<tournament_id>\d+)/$", tournament_registration, name="tournament_registration"),
    url(r"^riichi/(?P<slug>[\w\-]+)/$", tournament_details, name="tournament_details"),
    url(r"^riichi/(?P<slug>[\w\-]+)/announcement/$", tournament_announcement, name="tournament_announcement"),
]
