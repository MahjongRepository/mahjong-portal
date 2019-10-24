from django.conf.urls import url

from player.mahjong_soul.views import ms_accounts

urlpatterns = [
    url(r'^accounts/$', ms_accounts, name='ms_accounts'),
    url(r'^accounts/(?P<stat_type>[\w\-]+)/$', ms_accounts, name='ms_accounts'),
]
