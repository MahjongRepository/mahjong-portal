# -*- coding: utf-8 -*-

from django.contrib.auth import views as auth_views
from django.urls import path
from django.urls import re_path as url

from account.views import account_settings, do_login, request_player_and_user_connection


class CustomLogoutView(auth_views.LogoutView):
    def dispatch(self, request, *args, **kwargs):
        updated_request = request.POST.copy()
        updated_request.update({self.redirect_field_name: request.META.get("HTTP_REFERER", "/")})
        request.POST = updated_request
        return self.post(request, *args, **kwargs)


urlpatterns = [
    url(r"^logout/$", CustomLogoutView.as_view(), name="logout"),
    url(r"^login/$", do_login, name="do_login"),
    url(r"^settings/$", account_settings, name="account_settings"),
    path(
        r"request-verification/<slug:slug>/",
        request_player_and_user_connection,
        name="request_player_and_user_connection",
    ),
]
