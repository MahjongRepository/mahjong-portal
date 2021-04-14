from django.conf.urls import url
from django.contrib.auth import views as auth_views

from account.views import account_settings, sign_up

urlpatterns = [
    url(r"^login/$", auth_views.LoginView.as_view(template_name="account/login.html"), name="login"),
    url(r"^logout/$", auth_views.LogoutView.as_view(), name="logout"),
    url(r"^settings/$", account_settings, name="account_settings"),
    url(r"^sign-up/$", sign_up, name="sign_up"),
]
