from django.conf.urls import url

from tournament.views import tournament_list, tournament_details

urlpatterns = [
    url(r'^riichi/$', tournament_list, name='tournament_list'),
    url(r'^riichi/(?P<year>\d+)/$', tournament_list, name='tournament_list'),
    url(r'^riichi/(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/(?P<slug>[\w\-]+)/$', tournament_details, name='tournament_details'),
]
