from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.conf.urls import include, url

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^i18n/', include('django.conf.urls.i18n')),
]

urlpatterns += i18n_patterns(
    url(r'', include('website.urls')),
    url(r'^rating/', include('rating.urls')),
    url(r'^tournament/', include('tournament.urls')),
    url(r'^player/', include('player.urls')),
)
