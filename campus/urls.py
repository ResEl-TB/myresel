# -*- coding: utf-8 -*-

from django.conf.urls import url, include

from campus.views import home_view

urlpatterns = [
    url(r'^$', home_view, name='home'),
    url(r'^salles/', include('campus.suburls.urls_rooms', namespace='rooms')),
    url(r'^mails/', include('campus.suburls.urls_mails', namespace='mails')),
    url(r'^who/', include('campus.whoswho.urls', namespace='who')),
]