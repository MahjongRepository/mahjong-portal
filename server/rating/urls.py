from django.conf.urls import url

from rating.views import rating_details, rating_list, rating_tournaments

urlpatterns = [
    url(r'^riichi/list/$', rating_list, name='rating_list'),
    url(r'^riichi/(?P<slug>[\w\-]+)/$', rating_details, name='rating'),
    url(r'^riichi/(?P<slug>[\w\-]+)/(?P<country_code>[\w\-]+)/$', rating_details, name='rating'),
    url(r'^riichi/(?P<slug>[\w\-]+)/(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/$', rating_details, name='rating'),
    url(r'^riichi/(?P<slug>[\w\-]+)/tournaments/$', rating_tournaments, name='rating_tournaments'),
]
