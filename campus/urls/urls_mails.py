from django.conf.urls import url

from campus.views import sendMailView, moderate_view, rejectView

urlpatterns = [
    url(r'^$', sendMailView, name='send'),
    url(r'^modérer/$', moderate_view, name='moderate'),
    url(r'^rejeter/(?P<mail>[0-9]+)$', rejectView, name='reject'),
]