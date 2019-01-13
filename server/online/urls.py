from django.conf.urls import url

from online.views import add_user_to_the_pantheon

urlpatterns = [
    url(r'^add_user_to_the_pantheon/(?P<record_id>\d+)/$', add_user_to_the_pantheon, name='add_user_to_the_pantheon'),
]
