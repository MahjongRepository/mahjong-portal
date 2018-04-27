from django.conf.urls import url

from website.views import home, about, search, city_page, online_tournament_rules, contacts, get_current_tenhou_games

urlpatterns = [
    url(r'^$', home, name='home'),
    url(r'^about/$', about, name='about'),
    url(r'^contacts/$', contacts, name='contacts'),
    url(r'^online/$', online_tournament_rules, name='online'),
    url(r'^search/$', search, name='search'),
    url(r'^city/(?P<slug>[\w\-]+)/$', city_page, name='city_page'),
    url(r'^tenhou/games/$', get_current_tenhou_games, name='get_current_tenhou_games'),
]
