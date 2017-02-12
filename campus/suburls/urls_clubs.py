from django.conf.urls import url

from campus.subviews.views_clubs import list_clubs
from campus.views import sendMailView, moderateView, rejectView

urlpatterns = [
    url(r'^$', list_clubs, name='list'),
]