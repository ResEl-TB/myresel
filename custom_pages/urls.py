"""
custom_pages URL Conf
"""

from django.conf.urls import url
from .views import CategoryView, ArticleView, NewsListe

urlpatterns = [
    url(r'^news/', NewsListe.as_view(), name='news'),
    url(r'^(?P<category_slug>[-\w]+)/(?P<slug>[-\w]+)$', ArticleView.as_view(), name='show-article'),
    url(r'^(?P<slug>[-\w]+)$', CategoryView.as_view(), name='show-category'),
]
