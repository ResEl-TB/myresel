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

from .views import ManualAddDeviceView, ListDevicesView, EditDeviceView

app_name = 'devices'

urlpatterns = [
    url(r'^ajout-manuel$', ManualAddDeviceView.as_view(), name='ajout-manuel'),
    url(r'^liste$', ListDevicesView.as_view(), name='liste'),
    url(r'^modifier/(?P<mac>[A-Za-z0-9-]{2,})$', EditDeviceView.as_view(), name='modifier'),
]
