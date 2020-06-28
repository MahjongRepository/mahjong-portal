from django.conf.urls import include, url

from system.views import system_index, transliterate_text

urlpatterns = [
    url(r"^index/$", system_index, name="system_index"),
    url(r"^utils/transliterate/$", transliterate_text, name="transliterate_text"),
    url(r"^tournament/", include("system.tournament_admin.urls")),
    url(r"^players/", include("system.ema_players_admin.urls")),
]
