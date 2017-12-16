from django.conf.urls import url

from tournament.views import tournament_list, tournament_details

urlpatterns = [
    url(r'^list/$', tournament_list, name='tournament_list'),
    url(r'^(?P<tournament_slug>[\w\-]+)/$', tournament_details, name='tournament_details'),
]
