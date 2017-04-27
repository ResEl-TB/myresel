from django.conf.urls import url

from campus.views.views_clubs import list_clubs, NewClub, SearchClub

urlpatterns = [
    url(r'^$', list_clubs, name='list'),
    url(r'^nouveau$', NewClub.as_view(), name='new'),
    url(r'^search$', SearchClub.as_view(), name='search')
]
