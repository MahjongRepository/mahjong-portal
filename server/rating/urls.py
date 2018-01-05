from django.conf.urls import url

from rating.views import rating_details, rating_list

urlpatterns = [
    url(r'^riichi/list/$', rating_list, name='rating_list'),
    url(r'^riichi/(?P<slug>[\w\-]+)/$', rating_details, name='rating'),
    url(r'^riichi/(?P<slug>[\w\-]+)/(?P<page>\d+)/$', rating_details, name='rating'),
]
