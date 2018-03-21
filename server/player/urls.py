from django.conf.urls import url

from player.views import player_details, player_rating_details, player_by_id_details

urlpatterns = [
    url(r'^(?P<player_id>\d+)/$', player_by_id_details),
    url(r'^(?P<slug>[\w\-]+)/$', player_details, name='player_details'),
    url(r'^(?P<slug>[\w\-]+)/(?P<rating_slug>[\w\-]+)/details/$', player_rating_details, name='player_rating_details'),
]
