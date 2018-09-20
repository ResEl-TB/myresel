# -*- coding: utf-8 -*-

from django.conf.urls import url

from campus.views.views_ae_admin import AdminHome, GetUsers, GetMembers, \
EditFromCSV, AddAdmin

urlpatterns = [
    url(r'^$', AdminHome.as_view(), name='home'),
    url(r'^search-user$', GetUsers.as_view(), name='search-user'),
    url(r'^search-members$', GetMembers.as_view(), name='search-members'),
    url(r'^import-from-csv$', EditFromCSV.as_view(), name='import-from-csv'),
    url(r'^add-admin$', AddAdmin.as_view(), name='add-admin'),
]
