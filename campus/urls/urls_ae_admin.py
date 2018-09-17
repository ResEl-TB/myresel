# -*- coding: utf-8 -*-

from django.conf.urls import url

from campus.views.views_ae_admin import AdminHome, GetUsers, GetMembers

urlpatterns = [
    url(r'^$', AdminHome.as_view(), name='home'),
    url(r'^search-user$', GetUsers.as_view(), name='search-user'),
    url(r'^search-members$', GetMembers.as_view(), name='search-members'),
]
