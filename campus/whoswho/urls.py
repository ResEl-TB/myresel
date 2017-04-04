"""
pages URL Conf
"""

from django.conf.urls import url
from .views import RequestUser, UserDetails, AddBizu, UserHome, SearchUsers, RemovePerson

urlpatterns = [
    url(r'^request-user$', RequestUser.as_view(), name='request-user'),
    url(r'^search$', SearchUsers.as_view(), name='search-user'),
    url(r'^add-godchild$', AddBizu.as_view(), name='add-godchild'),
    url(r'^rm-godchild(?P<uid>[-\w]+)(?P<is_gp>True|False)', RemovePerson.as_view(), name='remove-person'),
    url(r'^(?P<uid>[-\w]+)', UserDetails.as_view(), name='user-details'),
    url(r'^$', UserHome.as_view(), name='user-home'),
]
