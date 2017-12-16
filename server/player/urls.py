from django.conf.urls import url

from player.views import player_details

urlpatterns = [
    url(r'^(?P<slug>[\w\-]+)/$', player_details, name='player_details'),
]
