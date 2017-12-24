from django.conf.urls import url
from django.views.generic import RedirectView

from campus.views import send_email_view, moderate_view, rejectView, display_mail

urlpatterns = [
    # url(r'^$', RedirectView.as_view(url="https://campus.resel.fr/?page=mailCampus/info", permanent=False), name='send'),
    url(r'^$', send_email_view, name='send'),
    url(r'^moderate/$', moderate_view, name='moderate'),
    url(r'^rejeter/(?P<mail>[0-9]+)$', rejectView, name='reject'),
    url(r'^display/(?P<mail>[0-9]+)$', display_mail, name='display')
]
