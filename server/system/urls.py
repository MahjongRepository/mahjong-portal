from django.conf.urls import url, include

from system.views import system_index

urlpatterns = [
    url(r'^index/$', system_index, name='system_index'),
    url(r'^tournament/', include('system.tournament_admin.urls')),
]
