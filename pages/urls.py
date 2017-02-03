
from django.conf.urls import url
from pages.views import NewsListe, FaqList, faqUpvote, NewsDetail

urlpatterns = [
    url(r'^news/$', NewsListe.as_view(), name='news'),
    url(r'^faq/$', FaqList.as_view(), name='faq'),
    url(r'^faq/upvote/$', faqUpvote, name='upvote'),
    ]
