from django.conf.urls import url

from campus.views.views_clubs import list_clubs, NewClub, SearchClub, EditClub, \
                                        DeleteClub, AddPersonToClub

urlpatterns = [
    url(r'^$', list_clubs, name='list'),
    url(r'^nouveau$', NewClub.as_view(), name='new'),
    url(r'^edit/(?P<pk>[a-z0-9]+)$', EditClub.as_view(), name='edit'),
    url(r'^search$', SearchClub.as_view(), name='search'),
    url(r'^remove/(?P<pk>[a-z0-9]+)$', DeleteClub.as_view(), name='delete'),
    url(r'^addself/(?P<pk>[a-z0-9]+)$', AddPersonToClub.as_view(), name='addself'),
    url(r'^addself/(?P<pk>[a-z0-9]+)/(?P<user>[a-z0-9]{0,})$', AddPersonToClub.as_view(), name='addperson'),
]
