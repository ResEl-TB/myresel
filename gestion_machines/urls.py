"""gestion_machines URL Configuration

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
from django.conf.urls import url
from .views import *

urlpatterns = [
    url(r'^réactivation$', Reactivation.as_view(), name = 'reactivation'),
    url(r'^ajout$', Ajout.as_view(), name = 'ajout'),
    url(r'^ajout-manuel$', AjoutManuel.as_view(), name = 'ajout-manuel'),
    url(r'^changement-campus$', ChangementCampus.as_view(), name = 'changement-campus'),
    url(r'^liste$', Liste.as_view(), name = 'liste'),
    url(r'^modifier/(?P<host>[a-z0-9-]{5,})$', Modifier.as_view(), name = 'modifier'),
]
