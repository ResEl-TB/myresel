
from django.conf.urls import url
from pages.views import NewsListe, FaqList, faqVote, NewsDetail, unsecure_set_language

urlpatterns = [
    url(r'^faq/$', FaqList.as_view(), name='faq'),
    url(r'^faq/upvote/$', faqVote, name='upvote'),
    ]
