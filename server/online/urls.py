from django.conf.urls import url

from online.views import add_user_to_the_pantheon, disable_user_in_pantheon

urlpatterns = [
    url(r"^add_user_to_the_pantheon/(?P<record_id>\d+)/$", add_user_to_the_pantheon, name="add_user_to_the_pantheon"),
    url(r"^disable_user_in_pantheon/(?P<record_id>\d+)/$", disable_user_in_pantheon, name="disable_user_in_pantheon"),
]
