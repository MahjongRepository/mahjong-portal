from django.contrib import admin
from django.conf.urls import include, url

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'', include('website.urls')),
    url(r'^rating/', include('rating.urls')),
]
