from django.conf.urls import url

from campus.views.views_clubs import list_clubs, NewClub, SearchClub, EditClub, \
                                     DeleteClub, AddPersonToClub, RemovePersonFromClub, \
                                     AddPrezToClub, MyClubs, ClubDetail, RequestClubs, AddMailToClub

urlpatterns = [
    url(r'^$', list_clubs, name='list'),
    url(r'^new$', NewClub.as_view(), name='new'),
    url(r'^edit/(?P<pk>[a-z0-9-]+)$', EditClub.as_view(), name='edit'),
    url(r'^search$', SearchClub.as_view(), name='search'),
    url(r'^remove/(?P<pk>[a-z0-9-]+)$', DeleteClub.as_view(), name='delete'),
    url(r'^addperson/(?P<pk>[a-z0-9-]+)$', AddPersonToClub.as_view(), name='add-person'),
    url(r'^addmail/(?P<pk>[a-z0-9-]+)$', AddMailToClub.as_view(), name='add-mail'),
    url(r'^removeperson/(?P<pk>[a-z0-9-]+)$', RemovePersonFromClub.as_view(), name='remove-person'),
    url(r'^addprez/(?P<pk>[a-z0-9-]+)$', AddPrezToClub.as_view(), name='add-prez'),
    url(r'^myclubs$', MyClubs.as_view(), name="my-clubs"),
    url(r'^fetch-clubs', RequestClubs.as_view(), name="getclubs"),
    url(r'^(?P<pk>[a-z0-9-]+)$', ClubDetail.as_view(), name="club_detail"),
]
