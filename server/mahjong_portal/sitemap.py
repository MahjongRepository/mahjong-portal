from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from club.models import Club
from player.models import Player
from rating.models import Rating
from tournament.models import Tournament


class BaseSitemap(Sitemap):
    i18n = True
    protocol = 'https'
    priority = 1


class StaticSitemap(BaseSitemap):
    changefreq = 'weekly'

    def items(self):
        return ['club_list', 'about']

    def location(self, item):
        return reverse(item)


class TournamentListSitemap(BaseSitemap):
    changefreq = 'monthly'

    def items(self):
        return [2018, 2017, 2016, 2015, 2014, 2013]

    def location(self, item):
        return reverse('tournament_list', kwargs={'year': item})


class EMATournamentListSitemap(TournamentListSitemap):
    changefreq = 'monthly'

    def location(self, item):
        return reverse('tournament_ema_list', kwargs={'year': item, 'tournament_type': 'EMA'})


class TournamentSitemap(BaseSitemap):
    changefreq = 'monthly'

    def items(self):
        return Tournament.objects.filter(is_upcoming=False).order_by('-end_date')

    def location(self, obj):
        return reverse('tournament_details', kwargs={'slug': obj.slug})

    def lastmod(self, obj):
        return obj.end_date


class TournamentAnnouncementSitemap(BaseSitemap):
    changefreq = 'weekly'

    def items(self):
        return Tournament.objects.filter(is_upcoming=True).order_by('-end_date')

    def location(self, obj):
        return reverse('tournament_announcement', kwargs={'slug': obj.slug})

    def lastmod(self, obj):
        return obj.updated_on


class ClubSitemap(BaseSitemap):
    changefreq = 'weekly'

    def items(self):
        return Club.objects.all()

    def location(self, obj):
        return reverse('club_details', kwargs={'slug': obj.slug})

    def lastmod(self, obj):
        return obj.updated_on


class PlayerSitemap(BaseSitemap):
    changefreq = 'weekly'

    def items(self):
        return Player.objects.all()

    def location(self, obj):
        return reverse('player_details', kwargs={'slug': obj.slug})

    def lastmod(self, obj):
        return obj.updated_on


class RatingSitemap(BaseSitemap):
    changefreq = 'weekly'

    def items(self):
        return Rating.objects.all()

    def location(self, obj):
        return reverse('rating', kwargs={'slug': obj.slug})

    def lastmod(self, obj):
        return obj.updated_on
