from django.conf.urls import url

from website.views import home, about, search, city_page, online_tournament_rules, contacts, \
    iormc_2018, erc_qualification_2019, export_tournament_results, rating_faq

urlpatterns = [
    url(r'^$', home, name='home'),
    url(r'^about/$', about, name='about'),
    url(r'^iormc/2018/$', iormc_2018, name='iormc_2018'),
    url(r'^erc/2019/$', erc_qualification_2019, name='erc_qualification_2019'),
    url(r'^rating/faq/$', rating_faq, name='rating_faq'),
    url(r'^contacts/$', contacts, name='contacts'),
    url(r'^online/$', online_tournament_rules, name='online'),
    url(r'^search/$', search, name='search'),
    url(r'^city/(?P<slug>[\w\-]+)/$', city_page, name='city_page'),
    url(r'^export_tournament_results/(?P<tournament_id>\d+)/$',
        export_tournament_results,
        name='export_tournament_results'),
]
