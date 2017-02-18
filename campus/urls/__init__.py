# -*- coding: utf-8 -*-

from django.conf.urls import url, include

from campus.views import home_view

urlpatterns = [
    url(r'^$', home_view, name='home'),
    url(r'^salles/', include('campus.urls.urls_rooms', namespace='rooms')),
    url(r'^mails/', include('campus.urls.urls_mails', namespace='mails')),
    url(r'^who/', include('campus.whoswho.urls', namespace='who')),
    url(r'^clubs/', include('campus.urls.urls_clubs', namespace='clubs')),
]