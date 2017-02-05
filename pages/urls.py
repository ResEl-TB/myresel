
from django.conf.urls import url
from pages.views import NewsListe, FaqList, faqUpvote, NewsDetail

urlpatterns = [
    url(r'^faq/$', FaqList.as_view(), name='faq'),
    url(r'^faq/upvote/$', faqUpvote, name='upvote'),
    ]
