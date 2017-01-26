from django.conf.urls import url

from campus.views import sendMailView, moderateView, rejectView

urlpatterns = [
    url(r'^$', sendMailView, name='send'),
    url(r'^modérer/$', moderateView, name='moderate'),
    url(r'^rejeter/(?P<mail>[0-9]+)$', rejectView, name='reject'),
]