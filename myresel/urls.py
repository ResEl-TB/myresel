"""myresel URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib.auth import views as auth_views
from django.contrib import admin
from django.conf.urls import handler400, handler403, handler404, handler500
from .views import *

urlpatterns = [
    url(r'^$', Home.as_view(), name = 'home'),
    url(r'^ckeditor/', include('ckeditor_uploader.urls')),
    url(r'^login/', auth_views.login),
    url(r'^logout/', auth_views.logout, {'next_page': '/'}),
    url(r'^gestion/', admin.site.urls),
    url(r'^news$', NewsListe.as_view(), name = 'news'),
    url(r'^machines/', include('gestion_machines.urls', namespace = 'gestion-machines')),
    url(r'^personnes/', include('gestion_personnes.urls', namespace = 'gestion-personnes')),
    url(r'^paiement/', include('tresorerie.urls', namespace = 'tresorerie')),
    url(r'^pages/', include('custom_pages.urls', namespace = 'custom-pages')),
    url(r'^contact$', Contact.as_view(), name = 'contact'),
]

handler400 = 'myresel.error_views.bad_request'
handler403 = 'myresel.error_views.permission_denied'
handler404 = 'myresel.error_views.page_not_found'
handler500 = 'myresel.error_views.server_error'
