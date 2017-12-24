from django.conf.urls import url

from club.views import club_list, club_details

urlpatterns = [
    url(r'^riichi/$', club_list, name='club_list'),
    url(r'^riichi/(?P<slug>[\w\-]+)/$', club_details, name='club_details'),
]
