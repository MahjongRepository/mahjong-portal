from django.conf.urls import url

from website.views import home, about, search

urlpatterns = [
    url(r'^$', home, name='home'),
    url(r'^about/$', about, name='about'),
    url(r'^search/$', search, name='search'),
]
