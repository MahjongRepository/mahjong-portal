from django.conf.urls import url

from ema.views import best_countries

urlpatterns = [
    url(r'^countries/best/$', best_countries, name='best_countries'),
]
