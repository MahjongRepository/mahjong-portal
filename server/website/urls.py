from django.conf.urls import url

from website.views import home, about, search, city_page

urlpatterns = [
    url(r'^$', home, name='home'),
    url(r'^about/$', about, name='about'),
    url(r'^search/$', search, name='search'),
    url(r'^city/(?P<slug>[\w\-]+)/$', city_page, name='city_page'),
]
