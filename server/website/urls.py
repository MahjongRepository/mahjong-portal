from django.conf.urls import url

from website.views import home, about, search, city_page, online_tournament_rules, contacts, get_current_tenhou_games, \
    get_current_tenhou_games_async, latest_yakumans, tenhou_accounts, iormc_2018

urlpatterns = [
    url(r'^$', home, name='home'),
    url(r'^about/$', about, name='about'),
    url(r'^iormc/2018/$', iormc_2018, name='iormc_2018'),
    url(r'^contacts/$', contacts, name='contacts'),
    url(r'^online/$', online_tournament_rules, name='online'),
    url(r'^search/$', search, name='search'),
    url(r'^city/(?P<slug>[\w\-]+)/$', city_page, name='city_page'),
    url(r'^tenhou/games/$', get_current_tenhou_games, name='get_current_tenhou_games'),
    url(r'^tenhou/games/async/$', get_current_tenhou_games_async, name='get_current_tenhou_games_async'),
    url(r'^tenhou/yakumans/$', latest_yakumans, name='latest_yakumans'),
    url(r'^tenhou/accounts/$', tenhou_accounts, name='tenhou_accounts'),
]
