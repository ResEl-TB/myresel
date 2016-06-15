"""
custom_pages URL Conf
"""

from django.conf.urls import url
from .views import seeCategory, seeArticle

urlpatterns = [
    url(r'(?P<slug>[-\w]+)$', CategoryView.as_view(), name = 'show-category' ),
    url(r'(?P<category_slug>[-\w]+)/(?P<slug>[-\w]+)', ArticleView.as_view(), name = 'show-article'),
]
