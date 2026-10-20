"""
pages URL Conf
"""

from django.urls import re_path
from .views import CategoryView, ArticleView

app_name = 'wiki'

urlpatterns = [
    re_path(r'^(?P<category_slug>[-\w]+)/(?P<slug>[-\w]+)$', ArticleView.as_view(), name='show-article'),
    re_path(r'^(?P<slug>[-\w]+)$', CategoryView.as_view(), name='show-category'),
]
