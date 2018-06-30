from django.conf.urls import url

from player.views import player_details, player_rating_details, player_by_id_details, player_tournaments, \
    player_by_id_tenhou_details, player_tenhou_details

urlpatterns = [
    url(r'^(?P<player_id>\d+)/$', player_by_id_details),
    url(r'^(?P<player_id>\d+)/tenhou/$', player_by_id_tenhou_details),
    url(r'^(?P<slug>[\w\-]+)/$', player_details, name='player_details'),
    url(r'^(?P<slug>[\w\-]+)/tenhou/$', player_tenhou_details, name='player_tenhou_details'),
    url(r'^(?P<slug>[\w\-]+)/tournaments/$', player_tournaments, name='player_tournaments'),
    url(r'^(?P<slug>[\w\-]+)/(?P<rating_slug>[\w\-]+)/details/$', player_rating_details, name='player_rating_details'),
]
