from django.conf.urls import url
from django.contrib.auth import views as auth_views
from django.urls import path

from account.views import account_settings, request_player_and_user_connection, sign_up

urlpatterns = [
    url(r"^login/$", auth_views.LoginView.as_view(template_name="account/login.html"), name="login"),
    url(r"^logout/$", auth_views.LogoutView.as_view(), name="logout"),
    url(r"^settings/$", account_settings, name="account_settings"),
    url(r"^sign-up/$", sign_up, name="sign_up"),
    path(
        r"request-verification/<slug:slug>/",
        request_player_and_user_connection,
        name="request_player_and_user_connection",
    ),
]
