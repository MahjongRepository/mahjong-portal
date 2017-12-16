from django.conf.urls import url

from rating.views import rating_list

urlpatterns = [
    url(r'^(?P<slug>[\w\-]+)/$', rating_list, name='rating'),
]
