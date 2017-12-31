from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.conf.urls import include, url
from django.contrib.sitemaps.views import sitemap
from django.views.decorators.cache import cache_page

from mahjong_portal.sitemap import TournamentSitemap, TournamentAnnouncementSitemap, ClubSitemap, PlayerSitemap, \
    RatingSitemap, StaticSitemap, TournamentListSitemap, EMATournamentListSitemap

sitemaps = {
    'static': StaticSitemap,
    'tournament_list': TournamentListSitemap,
    'ema_tournaments_list': EMATournamentListSitemap,
    'tournament_details': TournamentSitemap,
    'tournament_announcement_details': TournamentAnnouncementSitemap,
    'club_details': ClubSitemap,
    'player_details': PlayerSitemap,
    'rating_details': RatingSitemap,
}

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^i18n/', include('django.conf.urls.i18n')),

    url(r'^sitemap\.xml$', cache_page(86400)(sitemap), {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap')
]

urlpatterns += i18n_patterns(
    url(r'', include('website.urls')),
    url(r'^rating/', include('rating.urls')),
    url(r'^tournaments/', include('tournament.urls')),
    url(r'^clubs/', include('club.urls')),
    url(r'^players/', include('player.urls')),
    url(r'^system/', include('system.urls')),
)
