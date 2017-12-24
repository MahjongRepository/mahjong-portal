from django.conf.urls import url

from system.tournament_admin.views import new_tournaments, upload_results

urlpatterns = [
    url(r'^list/$', new_tournaments, name='new_tournaments'),
    url(r'^(?P<tournament_id>\d+)/upload/$', upload_results, name='upload_results'),
]
