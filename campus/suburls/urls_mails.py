from django.conf.urls import url

from campus.views import sendMailView, moderateView

urlpatterns = [
    url(r'^$', sendMailView, name='send'),
    url(r'^modérer/$', moderateView, name='moderate-list'),
    url(r'^modérer/(?P<mail>[0-9]+)/$', moderateView, name='moderate-specific'),
]