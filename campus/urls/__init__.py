# -*- coding: utf-8 -*-

from django.conf.urls import url, include

from campus.views.views_home import Home

urlpatterns = [
    url(r'^$', Home.as_view(), name='home'),
    url(r'^salles/', include('campus.urls.urls_rooms', namespace='rooms')),
    url(r'^mails/', include('campus.urls.urls_mails', namespace='mails')),
    url(r'^who/', include('campus.whoswho.urls', namespace='who')),
    url(r'^clubs/', include('campus.urls.urls_clubs', namespace='clubs')),
    url(r'^gestion/', include('campus.urls.urls_gestion', namespace='gestion')),
    url(r'^ae-admin/', include('campus.urls.urls_ae_admin', namespace='ae-admin')),
]
