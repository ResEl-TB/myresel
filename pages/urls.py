from django.urls import re_path
from pages.views import FaqList, faqVote, eggdrop

urlpatterns = [
    re_path(r'^faq/$', FaqList.as_view(), name='faq'),
    re_path(r'^faq/upvote/$', faqVote, name='upvote'),
    re_path(r'^eggdrop/$', eggdrop, name='eggdrop'),
    ]
