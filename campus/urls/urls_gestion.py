# -*- coding: utf-8 -*-

from django.conf.urls import url

from campus.views.views_gestion import ManageCampusModo, AddCampusModo, RemoveCampusModo

urlpatterns = [
    url(r'^modo/$', ManageCampusModo.as_view(), name='modo'),
    url(r'^del-modo/$', RemoveCampusModo.as_view(), name='delmodo'),
    url(r'^add-modo/$', AddCampusModo.as_view(), name='addmodo'),
]
