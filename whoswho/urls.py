"""
pages URL Conf
"""

from django.conf.urls import url
from .views import Godparents, UserDetails

urlpatterns = [
    url(r'^(?P<uid>[-\w]+)', UserDetails.as_view(), name='user-details'),
    url(r'^godparents$', Godparents.as_view(), name='godparents'),
]