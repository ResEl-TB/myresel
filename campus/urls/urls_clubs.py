from django.conf.urls import url

from campus.views.views_clubs import list_clubs, NewClub

urlpatterns = [
    url(r'^$', list_clubs, name='list'),
    url(r'^nouveau$', NewClub.as_view(), name='new'),
]