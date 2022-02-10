from django.conf.urls import url
from django.contrib.auth import views as auth_views
from django.urls import path

from account.views import account_settings, do_login, request_player_and_user_connection

urlpatterns = [
    url(r"^logout/$", auth_views.LogoutView.as_view(), name="logout"),
    url(r"^login/$", do_login, name="do_login"),
    url(r"^settings/$", account_settings, name="account_settings"),
    path(
        r"request-verification/<slug:slug>/",
        request_player_and_user_connection,
        name="request_player_and_user_connection",
    ),
]
