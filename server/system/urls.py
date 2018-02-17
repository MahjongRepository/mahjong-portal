from django.conf.urls import url, include

from system.views import system_index, transliterate_text

urlpatterns = [
    url(r'^index/$', system_index, name='system_index'),
    url(r'^utils/transliterate/$', transliterate_text, name='transliterate_text'),
    url(r'^tournament/', include('system.tournament_admin.urls')),
]
