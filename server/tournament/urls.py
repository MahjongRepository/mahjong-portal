from django.conf.urls import url

from tournament.views import tournament_list, tournament_details, tournament_announcement

urlpatterns = [
    url(r'^riichi/(?P<year>\d+)/$', tournament_list, name='tournament_list'),
    url(r'^riichi/(?P<tournament_type>[\w\-]+)/(?P<year>\d+)/$', tournament_list, name='tournament_ema_list'),

    url(r'^riichi/(?P<slug>[\w\-]+)/$', tournament_details, name='tournament_details'),
    url(r'^riichi/(?P<slug>[\w\-]+)/announcement/$', tournament_announcement, name='tournament_announcement'),
]
