"""
pages URL Conf
"""

from django.conf.urls import url
from .views import RequestUser, UserDetails, AddPerson, UserHome, SearchUsers, RemovePerson, ListBirthdays

urlpatterns = [
    url(r'^request-user$', RequestUser.as_view(), name='request-user'),
    url(r'^search$', SearchUsers.as_view(), name='search-user'),
    url(r'^add-person(?P<is_gp>True|False)$', AddPerson.as_view(), name='add-person'),
    url(r'^rm-person(?P<uid>[-\w]+)(?P<is_gp>True|False)', RemovePerson.as_view(), name='remove-person'),
    url(r'^birthdays$', ListBirthdays.as_view(), name='list-birthdays'),
    url(r'^(?P<uid>[-\w]+)', UserDetails.as_view(), name='user-details'),
    url(r'^$', UserHome.as_view(), name='user-home'),
]
