from django.conf.urls import url

from campus.views.views_clubs import list_clubs, NewClub, SearchClub, EditClub, \
                                        DeleteClub, AddPersonToClub, RemovePersonFromClub

urlpatterns = [
    url(r'^$', list_clubs, name='list'),
    url(r'^nouveau$', NewClub.as_view(), name='new'),
    url(r'^edit/(?P<pk>[a-z0-9]+)$', EditClub.as_view(), name='edit'),
    url(r'^search$', SearchClub.as_view(), name='search'),
    url(r'^remove/(?P<pk>[a-z0-9]+)$', DeleteClub.as_view(), name='delete'),
    url(r'^addperson/(?P<pk>[a-z0-9]+)$', AddPersonToClub.as_view(), name='addself'),
    url(r'^addperson/(?P<pk>[a-z0-9]+)/(?P<user>[a-z0-9]{0,})$',
        AddPersonToClub.as_view(), name='addperson'),
    url(r'^removeperson/(?P<pk>[a-z0-9]+)$', RemovePersonFromClub.as_view(), name='removeself'),
    url(r'^removeperson/(?P<pk>[a-z0-9]+)/(?P<user>[a-z0-9]{0,})$',
        RemovePersonFromClub.as_view(), name='removeperson'),
]
