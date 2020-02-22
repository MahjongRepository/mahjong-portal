from django.conf.urls import url

from ema.views import best_countries, ema_quotas

urlpatterns = [
    url(r"^countries/best/$", best_countries, name="best_countries"),
    url(r"^quotas/$", ema_quotas, name="ema_quotas"),
]
