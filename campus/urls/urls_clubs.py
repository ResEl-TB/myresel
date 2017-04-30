from django.conf.urls import url

from campus.views.views_clubs import list_clubs, NewClub, SearchClub, EditClub, DeleteClub

urlpatterns = [
    url(r'^$', list_clubs, name='list'),
    url(r'^nouveau$', NewClub.as_view(), name='new'),
    url(r'^edit/(?P<pk>[a-z0-9]+)$', EditClub.as_view(), name='edit'),
    url(r'^search$', SearchClub.as_view(), name='search'),
    url(r'^remove/(?P<pk>[a-z0-9]+)$', DeleteClub.as_view(), name='delete')
]
