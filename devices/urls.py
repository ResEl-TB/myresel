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

from .views import Reactivation, AddDeviceView, ManualAddDeviceView, ListDevicesView, EditDeviceView, BandwidthUsage

urlpatterns = [
    url(r'^réactivation$', Reactivation.as_view(), name='reactivation'),
    url(r'^ajout$', AddDeviceView.as_view(), name ='ajout'),
    url(r'^ajout-manuel$', ManualAddDeviceView.as_view(), name='ajout-manuel'),
    url(r'^liste$', ListDevicesView.as_view(), name='liste'),
    url(r'^modifier/(?P<host>[a-z0-9-]{2,})$', EditDeviceView.as_view(), name='modifier'),
    url(r'^consommation$', BandwidthUsage.as_view(), name='bandwidth-usage')
]