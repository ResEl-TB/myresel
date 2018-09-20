# -*- coding: utf-8 -*-

from django.conf.urls import url

from campus.views.views_ae_admin import AdminHome, GetUsers, GetMembers, \
EditFromCSV, AddAdmin, GetAdmins, DeleteAdmin

urlpatterns = [
    url(r'^$', AdminHome.as_view(), name='home'),
    url(r'^search-user$', GetUsers.as_view(), name='search-user'),
    url(r'^search-members$', GetMembers.as_view(), name='search-members'),
    url(r'^import-from-csv$', EditFromCSV.as_view(), name='import-from-csv'),
    url(r'^add-admin$', AddAdmin.as_view(), name='add-admin'),
    url(r'^get-admins$', GetAdmins.as_view(), name='get-admins'),
    url(r'^delete-admin$', DeleteAdmin.as_view(), name='delete-admin'),
]
